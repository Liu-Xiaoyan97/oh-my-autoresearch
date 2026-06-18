#!/usr/bin/env bash
# apply_model_config.sh — bootstrap 阶段将 objective.json 的模型配置填充到 agent .md 文件。
#
# 在 Phase 0 初始化时执行一次（幂等可重复）：
#   读取 objective.json["model"] 字典，将每个 subagent 对应的模型值直接写入
#   .claude/agents/<name>.md 的 model: 字段，替换 `$(resolve_model.sh ...)` 占位符。
#
# 这样 agent 的 .md 文件在 bootstrap 后就包含了最终的模型标识，
# team-lead spawn subagent 时无需再传 model 参数，.md 定义中的 model 直
# 接生效。
#
# 用法:
#   ./apply_model_config.sh <runtime_root>
# 示例:
#   ./apply_model_config.sh runtime

set -uo pipefail

RUNTIME_ROOT="${1:-runtime}"
OBJECTIVE_FILE="${RUNTIME_ROOT}/states/objective.json"

if [ ! -f "$OBJECTIVE_FILE" ]; then
    echo "[apply_model_config] objective.json 不存在，跳过"
    exit 0
fi

# .claude/agents/ 相对于 runtime_root 的路径
AGENTS_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/.claude/agents"

if [ ! -d "$AGENTS_DIR" ]; then
    echo "[apply_model_config] .claude/agents/ 目录不存在: $AGENTS_DIR"
    exit 0
fi

export PY_OBJECTIVE_FILE="${OBJECTIVE_FILE}"
export PY_AGENTS_DIR="${AGENTS_DIR}"

python3 << 'PYEOF'
import json, os, re, sys

objective_file = os.environ['PY_OBJECTIVE_FILE']
agents_dir = os.environ['PY_AGENTS_DIR']

try:
    obj = json.load(open(objective_file))
    models = obj.get('model', {})
except Exception as e:
    print(f'[apply_model_config] 读取 objective.json 失败: {e}', file=sys.stderr)
    sys.exit(0)

if not isinstance(models, dict):
    print('[apply_model_config] model 不是字典，跳过')
    sys.exit(0)

if isinstance(models, str):
    print('[apply_model_config] model 是字符串格式（旧版兼容），跳过')
    sys.exit(0)

updated = []
skipped = []

for agent_name, model_value in models.items():
    if agent_name == 'default':
        continue
    if not isinstance(model_value, str) or not model_value.strip():
        continue

    md_file = os.path.join(agents_dir, f'{agent_name}.md')
    if not os.path.exists(md_file):
        skipped.append(f'{agent_name}（文件不存在）')
        continue

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换占位符: model: $(resolve_model.sh runtime <agent_name>)
    # 用 [$] 匹配字面 $（\$ 在 re 中被解释为行尾锚点）
    placeholder_pattern = re.compile(
        r'^model:\s*[$]\s*\(resolve_model\.sh\s+\S+\s+' + re.escape(agent_name) + r'\s*\)',
        re.MULTILINE
    )
    new_content, count = placeholder_pattern.subn(f'model: {model_value.strip()}', content)

    if count > 0:
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated.append(f'{agent_name} → {model_value.strip()}')
    else:
        loose_pattern = re.compile(
            r'^model:\s*.*resolve_model\.sh.*' + re.escape(agent_name) + r'.*',
            re.MULTILINE
        )
        if not loose_pattern.search(content):
            skipped.append(f'{agent_name}（无占位符）')

if updated:
    print(f'[apply_model_config] 已填充 {len(updated)} 个 agent:')
    for u in updated:
        print(f'  - {u}')
else:
    print('[apply_model_config] 无 agent 需要更新')

if skipped:
    for s in skipped:
        print(f'  [跳过] {s}')
PYEOF