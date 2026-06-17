#!/usr/bin/env python3
"""generate_observation.py - 自治观察者的 LLM 观察生成（best-effort）。

由 observer daemon 在一轮迭代收尾(state current_step=9)时触发，绝不阻塞主程序——
主程序只 emit 事件，从不调用本模块。流程：
  1. 读独立 LLM 配置 observer/llm.config.json(缺失回退 example, 无 key 则禁用)。
  2. 汇总该 exp_name 的一轮数据(states/exploration/experiments/训练日志尾)。
  3. 调 Anthropic 兼容 /v1/messages 生成中文 observation + 一行 INSIGHT。
  4. 存到 observer 自己的库/日志(observation_store)。
  5. 把 INSIGHT 追加到 knowledges(默认 learned.json, 带 [observer] 标记)供下一轮参考。
任何失败都被吞掉(返回 skipped/error)，不影响确定性写入与 offset 推进。
"""

import json
import sqlite3
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
from observation_store import append as store_append  # noqa: E402


def _load_cfg(runtime_root: str) -> dict:
    base = Path(runtime_root) / "observer"
    for name in ("llm.config.json", "llm.config.example.json"):
        p = base / name
        if p.exists():
            cfg = json.loads(p.read_text(encoding="utf-8"))
            cfg["_source"] = name
            return cfg
    return {"enabled": False}


def _experiments_row(runtime_root: str, exp_name: str):
    db = Path(runtime_root) / "db" / "runtime.sqlite"
    if not db.exists():
        return None
    conn = sqlite3.connect(str(db))
    try:
        cols = [r[1] for r in conn.execute('PRAGMA table_info(experiments)')]
        row = conn.execute("SELECT * FROM experiments WHERE exp_name=?", (exp_name,)).fetchone()
        return dict(zip(cols, row)) if row else None
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def _exploration_row(runtime_root: str, exp_name: str):
    db = Path(runtime_root) / "db" / "runtime.sqlite"
    if not db.exists():
        return None
    conn = sqlite3.connect(str(db))
    try:
        cols = [r[1] for r in conn.execute('PRAGMA table_info(exploration)')]
        row = conn.execute("SELECT * FROM exploration WHERE exp_name=?", (exp_name,)).fetchone()
        return dict(zip(cols, row)) if row else None
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def _gather(runtime_root: str, exp_name: str) -> dict:
    rr = Path(runtime_root)
    ctx = {"exp_name": exp_name}
    sp = rr / "states" / "states.json"
    if sp.exists():
        ctx["states"] = json.loads(sp.read_text(encoding="utf-8"))
    op = rr / "states" / "objective.json"
    if op.exists():
        ctx["objective"] = json.loads(op.read_text(encoding="utf-8"))
    bp = rr / "knowledges" / "baseline.json"
    if bp.exists():
        ctx["baseline"] = json.loads(bp.read_text(encoding="utf-8"))
    ctx["exploration"] = _exploration_row(runtime_root, exp_name)
    ctx["experiments"] = _experiments_row(runtime_root, exp_name)
    log = rr / "logs" / f"train-of-{exp_name}.log"
    if log.exists():
        ctx["train_log_tail"] = "\n".join(log.read_text(errors="ignore").splitlines()[-30:])
    return ctx


def _call_llm(cfg: dict, system: str, user: str) -> str:
    url = cfg["base_url"].rstrip("/") + "/v1/messages"
    body = json.dumps({
        "model": cfg["model"],
        "max_tokens": cfg.get("max_tokens", 1024),
        "temperature": cfg.get("temperature", 0.3),
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "content-type": "application/json",
        "x-api-key": cfg["api_key"],
        "anthropic-version": cfg.get("anthropic_version", "2023-06-01"),
    })
    with urllib.request.urlopen(req, timeout=cfg.get("timeout", 60)) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    return "".join(parts).strip()


def generate(runtime_root: str, exp_name: str) -> dict:
    cfg = _load_cfg(runtime_root)
    if not cfg.get("enabled") or not cfg.get("api_key") or not cfg.get("model"):
        return {"skipped": True, "reason": "LLM 未启用或缺少 api_key/model"}

    ctx = _gather(runtime_root, exp_name)
    system = (
        "你是 oh-my-autoresearch 的自治研究观察者(observer)。你独立运行，不被主程序调用，"
        "只基于事件驱动的数据做观察。请用简洁中文，对给定的一轮实验给出 observation，"
        "涵盖：方向探索/票选决策的要点、训练主指标随 eval 检查点的变化趋势、与 baseline 的对比判断。"
        "最后另起一行，以 'INSIGHT: ' 开头给出一句可供下一轮参考的洞见。"
    )
    user = "本轮实验数据(JSON)：\n" + json.dumps(ctx, ensure_ascii=False, indent=2)

    try:
        text = _call_llm(cfg, system, user)
    except Exception as e:
        return {"skipped": False, "error": f"LLM 调用失败: {e}"}
    if not text:
        return {"skipped": False, "error": "LLM 返回空"}

    insight = ""
    for line in text.splitlines():
        if line.strip().upper().startswith("INSIGHT:"):
            insight = line.split(":", 1)[1].strip()
            break

    states = ctx.get("states", {})
    store_append(runtime_root, {
        "exp_name": exp_name,
        "iteration": states.get("iteration"),
        "current_step": states.get("current_step"),
        "observation": text,
        "insight": insight,
    })

    # 洞见回灌 knowledges(best-effort, 带 [observer] 标记, 不与 team-lead 的权威判定冲突)
    if insight:
        try:
            target = cfg.get("feedback_target", "learned")
            sys.path.insert(0, str(HERE.parents[2] / "scripts" / "writers"))
            import write_knowledge
            decision = (ctx.get("exploration") or {}).get("decision", "")
            action = "append_rejected" if target == "rejected" else "append_learned"
            write_knowledge.write(runtime_root, {
                "action": action,
                "data": {
                    "exp_name": exp_name,
                    "method_summary": (decision[:200] if isinstance(decision, str) else str(decision)[:200]) or "(observer)",
                    "reason": "[observer] " + insight,
                },
            })
        except Exception as e:
            print(f"[generate_observation] 洞见回灌失败(忽略): {e}", file=sys.stderr)

    return {"skipped": False, "stored": True, "insight": insight,
            "observation_chars": len(text)}


if __name__ == "__main__":
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    exp_name = sys.argv[2] if len(sys.argv) > 2 else ""
    print(json.dumps(generate(runtime_root, exp_name), ensure_ascii=False))
