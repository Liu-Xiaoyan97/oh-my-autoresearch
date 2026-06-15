#!/usr/bin/env bash
set -euo pipefail

# generate_launch.sh - 生成训练 launch script
# 输出: runtime/launchscripts/launch_<exp_name>.sh
# 用法:
#   generate_launch.sh [runtime_root]
#   generate_launch.sh <runtime_root> <exp_name> <command>

RUNTIME_ROOT="${1:-runtime}"
EXP_NAME="${2:-}"
COMMAND="${3:-}"

if [[ -z "$EXP_NAME" ]] || [[ -z "$COMMAND" ]]; then
    METADATA="$(python3 - "$RUNTIME_ROOT" <<'PY'
import json
import shlex
import sys
from pathlib import Path

runtime_root = Path(sys.argv[1])
objective = json.loads((runtime_root / "states" / "objective.json").read_text(encoding="utf-8"))
states = json.loads((runtime_root / "states" / "states.json").read_text(encoding="utf-8"))

command = objective["command"]
num_steps = objective.get("num_training_steps")
eval_steps = objective.get("eval_n_steps")
args = []
if num_steps is not None:
    args.extend(["--num_training_steps", str(num_steps)])
if eval_steps is not None:
    args.extend(["--eval_n_steps", str(eval_steps)])

print(json.dumps({
    "exp_name": states.get("exp_name", "exp_0"),
    "project_root": objective.get("project_root", "."),
    "command": " ".join([command, *map(shlex.quote, args)]).strip(),
}, ensure_ascii=False))
PY
)"
    EXP_NAME="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["exp_name"])' "$METADATA")"
    PROJECT_ROOT="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["project_root"])' "$METADATA")"
    COMMAND="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["command"])' "$METADATA")"
else
    PROJECT_ROOT="$RUNTIME_ROOT"
fi

LAUNCH_DIR="$RUNTIME_ROOT/launchscripts"
mkdir -p "$LAUNCH_DIR"

LAUNCH_SCRIPT="$LAUNCH_DIR/launch_${EXP_NAME}.sh"

cat > "$LAUNCH_SCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail
# Launch script for: $EXP_NAME
# Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)

cd "$PROJECT_ROOT"
$COMMAND
EOF

chmod +x "$LAUNCH_SCRIPT"
echo "$LAUNCH_SCRIPT"
