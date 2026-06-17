#!/usr/bin/env python3
"""write_candidate_pool.py - 维护 knowledges/candidate_pool.json。

候选池是跨轮次共享的正交候选集文件，格式为 [{"name": "<方法名>", "description": "<描述>"}]。
作用：
  - 每轮探索生成的新候选集合并入池中（update，语义去重 + name 去重）。
  - 某候选被票选选中实验后从池中删除（remove），避免重复实验。
  - candidate_pool clear: 将池文件清空为 []（loop-reset 使用）。

事件：
  - candidate_pool update: 与现有池合并，新候选按 name + 语义相似度去重追加。
    如果新候选的描述与池中某候选高度相似（但 name 不同），替换旧候选。
  - candidate_pool remove: 从池中删除 payload.data.name 匹配的候选。
  - candidate_pool clear: 将池文件清空为 []（loop-reset 使用）。
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "database"))
from schema_spec import CANDIDATE_POOL_PATH

# 语义相似度阈值（Jaccard 字符 n-gram，0~1）
# 0.40 能覆盖 "parallel-branch-init-balance" vs "parallel-block-branch-init-balance"
# 且不会误杀描述截然不同的候选
SIMILARITY_THRESHOLD = 0.35

# 英文停用词，不携带语义信号，避免 inflate 相似度
_STOPS = frozenset({
    'the', 'a', 'an', 'of', 'in', 'to', 'from', 'for', 'at', 'by', 'on',
    'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might',
    'this', 'that', 'these', 'those',
    'it', 'its', 'each', 'per', 'so',
    'and', 'or', 'but', 'not', 'no', 'nor',
    'with', 'without', 'as', 'than', 'then', 'also',
    'only', 'more', 'less', 'very', 'just',
    'about', 'above', 'after', 'all', 'any', 'both',
    'some', 'such', 'which', 'while',
    'how', 'what', 'when', 'where', 'why',
    'up', 'down', 'out', 'off', 'over', 'under',
    'again', 'further', 'once', 'here', 'there',
    'can', 'shall', 'few',
})


def _tokens(text: str) -> set:
    """将文本拆分为 token 集合（英文单词 + 中文字符 + 数字）。

    英文按单词拆分（去掉停用词），中文逐字拆分，均转为小写。
    例如 'SwiGLU 乘积方差补偿' → {'swiglu', '乘', '积', '方', '差', '补', '偿'}
    """
    text = text.lower()
    tokens = set()
    # 英文单词/数字
    for m in re.finditer(r"[a-z][a-z0-9_]*", text):
        tok = m.group()
        if tok not in _STOPS:
            tokens.add(tok)
    # 中文字符逐字
    for ch in text:
        if '一' <= ch <= '鿿':
            tokens.add(ch)
    return tokens


def _desc_similarity(desc1: str, desc2: str) -> float:
    """计算两个候选描述的语义相似度（Jaccard token 集合）。

    中英文均支持：英文按单词、中文按单字、数字按 token。
    """
    if not desc1 or not desc2:
        return 0.0
    tokens1 = _tokens(desc1)
    tokens2 = _tokens(desc2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    return len(intersection) / len(union)


def _candidate_similarity(a: dict, b: dict) -> float:
    """综合计算两个候选的相似度 = max(name_similarity, desc_similarity)。

    候选 name 共享关键 token（如 'branch-init', 'embed-gain', 'gradient-clip'）
    即使描述语言不同也能捕获。
    """
    name_sim = _desc_similarity(a.get("name", ""), b.get("name", ""))
    desc_sim = _desc_similarity(a.get("description", ""), b.get("description", ""))
    return max(name_sim, desc_sim)


def write(runtime_root: str, payload: dict) -> bool:
    action = payload.get("action", "")
    data = payload.get("data", {})

    pool_file = Path(runtime_root) / CANDIDATE_POOL_PATH

    try:
        if action == "update":
            new_candidates = data.get("candidates", [])
            if not isinstance(new_candidates, list):
                print("[write_candidate_pool] data.candidates 必须是数组", file=sys.stderr)
                return False
            pool_file.parent.mkdir(parents=True, exist_ok=True)
            # 读取现有池
            existing = []
            if pool_file.exists():
                try:
                    existing = json.loads(pool_file.read_text(encoding="utf-8"))
                    if not isinstance(existing, list):
                        existing = []
                except (json.JSONDecodeError, TypeError):
                    existing = []

            # 建立 name → entry 映射和候选池
            pool = list(existing)  # 当前候选列表
            removed_names = []     # 被语义去重移除的候选名

            for c in new_candidates:
                if not isinstance(c, dict) or not c.get("name"):
                    continue
                new_name = c["name"]

                # Step 1: 按 name 精确去重
                already_by_name = any(
                    e.get("name") == new_name for e in pool if isinstance(e, dict)
                )
                if already_by_name:
                    continue

                # Step 2: 按语义相似度去重 —— 检测新候选是否与池中某候选高度相似
                duplicate_idx = None
                for i, e in enumerate(pool):
                    if not isinstance(e, dict) or not e.get("description"):
                        continue
                    sim = _candidate_similarity(c, e)
                    if sim >= SIMILARITY_THRESHOLD:
                        duplicate_idx = i
                        break

                if duplicate_idx is not None:
                    # 用新候选替换语义重复的旧候选
                    old_name = pool[duplicate_idx].get("name", "")
                    removed_names.append(old_name)
                    pool[duplicate_idx] = c
                    print(
                        f"[write_candidate_pool] 语义去重: '{old_name}' → '{new_name}' "
                        f"(相似度 {sim:.2f})"
                    )
                else:
                    pool.append(c)

            # Step 3: 池内语义去重 —— 池中候选彼此语义相似则保留描述更详细的一个
            intra_removed = []
            i = 0
            while i < len(pool):
                j = i + 1
                recheck = False
                while j < len(pool):
                    sim = _candidate_similarity(pool[i], pool[j])
                    if sim >= SIMILARITY_THRESHOLD:
                        desc_i = len(pool[i].get("description", ""))
                        desc_j = len(pool[j].get("description", ""))
                        if desc_i >= desc_j:
                            # 保留 i，移除 j
                            removed_name = pool[j].get("name", "")
                            intra_removed.append(removed_name)
                            pool.pop(j)
                            # j 自动前进到下一个
                        else:
                            # 保留 j，移除 i
                            removed_name = pool[i].get("name", "")
                            intra_removed.append(removed_name)
                            pool.pop(i)
                            recheck = True
                            break  # 从新 i 开始重新检查
                    else:
                        j += 1
                if not recheck:
                    i += 1

            # 原子写
            tmp = pool_file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(pool, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            tmp.replace(pool_file)

            added = len(pool) - len(existing)
            intra_n = len(intra_removed)
            all_removed = list(set(removed_names + intra_removed))
            if intra_n:
                sim_note = (
                    f"，池内去重 {intra_n} 个: {', '.join(intra_removed)}"
                )
            else:
                sim_note = ""
            print(
                f"[write_candidate_pool] 合并后 {len(pool)} 个候选 "
                f"（新增 {added}，替换 {len(removed_names)} 个语义重复{sim_note}）"
            )
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

        elif action == "clear":
            pool_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = pool_file.with_suffix(".json.tmp")
            tmp.write_text("[]\n", encoding="utf-8")
            tmp.replace(pool_file)
            print("[write_candidate_pool] 清空候选池")
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
