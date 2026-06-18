#!/usr/bin/env bash
# resolve_templates.sh — 从 objective.json + 模板文件生成最终 CLAUDE.md 和 agents/*.md。
#
# 替换占位符：
#   {{goal}}            → objective.json["goal"]
#   {{poll_interval}}   → objective.json["poll_interval"]
#   {{model.<name>}}    → objective.json["model"][<name>]
#
# 在 session-start hook 中自动执行，确保每次启动配置最新。
# 幂等可重复。
#
# 用法:
#   ./resolve_templates.sh <runtime_root>
# 示例:
#   ./resolve_templates.sh runtime

set -uo pipefail

RUNTIME_ROOT="${1:-runtime}"
OBJECTIVE_FILE="${RUNTIME_ROOT}/states/objective.json"
CLAUDE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)/.claude"

if [ ! -f "$OBJECTIVE_FILE" ]; then
    echo "[resolve_templates] objective.json 不存在: $OBJECTIVE_FILE"
    exit 0
fi

if [ ! -d "$CLAUDE_DIR" ]; then
    echo "[resolve_templates] .claude/ 目录不存在: $CLAUDE_DIR"
    exit 0
fi

export RUNTIME_ROOT CLAUDE_DIR

python3 << 'PYEOF'
import json, os, re, sys

runtime_root = os.environ['RUNTIME_ROOT']
claude_dir = os.environ['CLAUDE_DIR']
objective_file = os.path.join(runtime_root, 'states', 'objective.json')

# 读取 objective.json
try:
    with open(objective_file, 'r', encoding='utf-8') as f:
        objective = json.load(f)
except Exception as e:
    print(f'[resolve_templates] 读取 objective.json 失败: {e}', file=sys.stderr)
    sys.exit(0)

# 提取替换值
goal = objective.get('goal', '')
poll_interval = str(objective.get('poll_interval', 2))
model_map = objective.get('model', {})
if isinstance(model_map, str):
    # 兼容旧格式：model 为单个字符串
    model_map = {}

# 构建替换映射
replacements = {
    '{{goal}}': goal,
    '{{poll_interval}}': poll_interval,
}
for key, value in model_map.items():
    if isinstance(value, str):
        replacements[f'{{{{model.{key}}}}}'] = value.strip()

# 编译正则：匹配所有 {{...}} 占位符
placeholder_re = re.compile(r'\{\{([^}]+)\}\}')

def replace_all(text: str) -> str:
    """替换文本中所有 {{...}} 占位符。未匹配的占位符保留原样。"""
    def _replacer(m):
        key = m.group(0)  # 完整匹配如 {{model.coder}}
        if key in replacements:
            return replacements[key]
        return key  # 未匹配则保留
    return placeholder_re.sub(_replacer, text)

updated = []
skipped = []

# 处理 agents/*.md（优先用目录下同名 {{model.<name>}} 替换）
agents_dir = os.path.join(claude_dir, 'agents')
if os.path.isdir(agents_dir):
    for fname in sorted(os.listdir(agents_dir)):
        if not fname.endswith('.md'):
            continue
        path = os.path.join(agents_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            skipped.append(f'{fname}（读取失败: {e}）')
            continue

        new_content = replace_all(content)
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated.append(f'agents/{fname}')
        else:
            skipped.append(f'agents/{fname}（无占位符）')

# 处理 CLAUDE.md
claude_md = os.path.join(claude_dir, 'CLAUDE.md')
if os.path.exists(claude_md):
    try:
        with open(claude_md, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        skipped.append(f'CLAUDE.md（读取失败: {e}）')

    new_content = replace_all(content)
    if new_content != content:
        with open(claude_md, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated.append('CLAUDE.md')
    else:
        skipped.append('CLAUDE.md（无占位符）')
else:
    skipped.append('CLAUDE.md（不存在）')

if updated:
    print(f'[resolve_templates] 已填充 {len(updated)} 个文件:')
    for u in updated:
        print(f'  - {u}')
else:
    print('[resolve_templates] 无文件需要更新')

if skipped:
    for s in skipped:
        print(f'  [跳过] {s}')
PYEOF
