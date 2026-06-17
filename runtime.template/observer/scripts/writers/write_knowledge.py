#!/usr/bin/env python3
"""write_knowledge.py - 写入 baseline / learned / rejected JSON。

必须使用原子写，避免 JSON 损坏。
"""

import json
import sqlite3
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT / "utils"))
sys.path.insert(0, str(SCRIPTS_ROOT / "database"))
from atomic_write import atomic_write
from schema_spec import DB_PATH, states_exp_name


def write(runtime_root: str, payload: dict) -> bool:
    """根据 action 写入 knowledge 文件。"""
    action = payload.get("action", "")
    default_target = {
        "update_baseline": "baseline.json",
        "append_learned": "learned.json",
        "append_rejected": "rejected.json",
    }.get(action, "")
    target_file = payload.get("target_file") or default_target
    data = payload.get("data", {})
    # exp_name 文件优先：knowledge 条目恒指向当前实验，从 states.json 权威获取
    if isinstance(data, dict):
        resolved = states_exp_name(runtime_root) or data.get("exp_name", "")
        if resolved:
            data = {**data, "exp_name": resolved}

        # method_summary 自动解析：优先从 exploration 表的 decision 列读取
        # decision 已被 write_exploration._resolve_decision_name 解析为候选名
        ms = data.get("method_summary", "")
        if not ms or ms.startswith("candidate_"):
            try:
                db_path = Path(runtime_root) / DB_PATH
                if db_path.exists():
                    conn = sqlite3.connect(str(db_path))
                    row = conn.execute(
                        'SELECT "decision" FROM exploration WHERE exp_name = ?',
                        (data.get("exp_name", ""),),
                    ).fetchone()
                    conn.close()
                    if row and row[0]:
                        raw = row[0]
                        try:
                            decision_name = json.loads(raw)
                        except (json.JSONDecodeError, TypeError):
                            decision_name = raw
                        if isinstance(decision_name, str) and decision_name and \
                           not decision_name.startswith("candidate_"):
                            data["method_summary"] = decision_name
            except Exception:
                pass  # 解析失败不影响主流程

        # commit_id 自动解析：update_baseline 时从 exploration 表的 commit 列读取（文件优先）
        if action == "update_baseline" and isinstance(data, dict):
            commit_id = data.get("commit_id", "")
            if not commit_id:
                try:
                    db_path = Path(runtime_root) / DB_PATH
                    if db_path.exists():
                        conn = sqlite3.connect(str(db_path))
                        row = conn.execute(
                            'SELECT "commit" FROM exploration WHERE exp_name = ?',
                            (data.get("exp_name", ""),),
                        ).fetchone()
                        conn.close()
                        if row and row[0]:
                            commit_id = row[0]
                except Exception:
                    pass
            if commit_id:
                data = {**data, "commit_id": commit_id}

    knowledge_dir = Path(runtime_root) / "knowledges"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    if target_file not in {"baseline.json", "learned.json", "rejected.json"}:
        print(f"[write_knowledge] 非法 target_file: {target_file}", file=sys.stderr)
        return False
    file_path = knowledge_dir / target_file

    try:
        if not target_file:
            print(f"[write_knowledge] 未知 action 或 target_file 为空: {action}", file=sys.stderr)
            return False

        if action == "update_baseline":
            atomic_write(file_path, data)

        elif action == "append_learned":
            existing = []
            if file_path.exists():
                existing = json.loads(file_path.read_text(encoding="utf-8"))
            existing.append(data)
            atomic_write(file_path, existing)

        elif action == "append_rejected":
            existing = []
            if file_path.exists():
                existing = json.loads(file_path.read_text(encoding="utf-8"))
            existing.append(data)
            atomic_write(file_path, existing)

        else:
            print(f"[write_knowledge] 未知 action: {action}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        print(f"[write_knowledge] 错误: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    import sys
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
