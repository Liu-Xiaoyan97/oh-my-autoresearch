#!/usr/bin/env python3
"""write_candidate_pool.py - 维护 knowledges/candidate_pool.json。

候选池是跨轮次共享的正交候选集文件，格式为 [{"name": "<方法名>", "description": "<描述>"}]。
作用：
  - 每轮探索生成的新候选集写入池中（update），供后续轮次直接召回。
  - 某候选被票选选中实验后从池中删除（remove），避免重复实验。

事件：
  - candidate_pool update: 用 payload.data.candidates 数组覆盖池文件。
  - candidate_pool remove: 从池中删除 payload.data.name 匹配的候选。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "database"))
from schema_spec import CANDIDATE_POOL_PATH


def write(runtime_root: str, payload: dict) -> bool:
    action = payload.get("action", "")
    data = payload.get("data", {})

    pool_file = Path(runtime_root) / CANDIDATE_POOL_PATH

    try:
        if action == "update":
            candidates = data.get("candidates", [])
            if not isinstance(candidates, list):
                print("[write_candidate_pool] data.candidates 必须是数组", file=sys.stderr)
                return False
            pool_file.parent.mkdir(parents=True, exist_ok=True)
            # 原子写
            tmp = pool_file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(pool_file)
            print(f"[write_candidate_pool] 写入 {len(candidates)} 个候选")
            return True

        elif action == "remove":
            name_to_remove = data.get("name", "")
            if not name_to_remove:
                print("[write_candidate_pool] remove 需要 data.name", file=sys.stderr)
                return False
            if not pool_file.exists():
                print("[write_candidate_pool] 候选池文件不存在，无需删除", file=sys.stderr)
                return True

            pool = json.loads(pool_file.read_text(encoding="utf-8"))
            if not isinstance(pool, list):
                print("[write_candidate_pool] 候选池格式错误，不是数组", file=sys.stderr)
                return False

            before = len(pool)
            pool = [c for c in pool if c.get("name") != name_to_remove]
            removed = before - len(pool)

            # 原子写
            tmp = pool_file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(pool, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(pool_file)

            print(f"[write_candidate_pool] 删除 '{name_to_remove}'，移除 {removed} 个候选，剩余 {len(pool)}")
            return True

        else:
            print(f"[write_candidate_pool] 未知 action: {action}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"[write_candidate_pool] 错误: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    ok = write(runtime_root, payload)
    sys.exit(0 if ok else 1)
