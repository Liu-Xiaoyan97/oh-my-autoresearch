#!/usr/bin/env bash
set -euo pipefail

# generate_launch.sh - 生成训练 launch script
#
# 输出:
#   <project_root>/launchscripts/launch_<exp_name>.sh
#
# 用法:
#   generate_launch.sh [runtime_root]
#   generate_launch.sh <runtime_root> <exp_name> <command>
#
# 说明:
#   objective.command 应该是完整训练命令，例如：
#     "python train.py"
#     "python scripts/train.py --config configs/base.yaml"
#     "bash train.sh"
#
#   本脚本会自动追加：
#     --num_training_steps <num_training_steps>
#     --eval_n_steps <eval_n_steps>

RUNTIME_ROOT="${1:-runtime}"
EXP_NAME="${2:-}"
COMMAND="${3:-}"

if [[ -z "$EXP_NAME" ]] || [[ -z "$COMMAND" ]]; then
    METADATA="$(python3 - "$RUNTIME_ROOT" <<'PY'
import json
import sys
from pathlib import Path

runtime_root = Path(sys.argv[1]).resolve()
host_root = runtime_root.parent

objective_path = runtime_root / "states" / "objective.json"
states_path = runtime_root / "states" / "states.json"

objective = json.loads(objective_path.read_text(encoding="utf-8"))
states = json.loads(states_path.read_text(encoding="utf-8"))

command = objective["command"]

num_steps = objective.get("num_training_steps")
eval_steps = objective.get("eval_n_steps")
devices = objective.get("devices") or ["mps"]

extra_args = []
if num_steps is not None:
    extra_args.extend(["--num_training_steps", str(num_steps)])
if eval_steps is not None:
    extra_args.extend(["--eval_n_steps", str(eval_steps)])

project_root = Path(objective.get("project_root", "."))
if not project_root.is_absolute():
    project_root = host_root / project_root

normalized_devices = [str(device).strip() for device in devices if str(device).strip()]
if not normalized_devices:
    normalized_devices = ["mps"]

cuda_ids = []
use_mps = False

for device in normalized_devices:
    lower = device.lower()
    if lower == "mps":
        use_mps = True
    elif lower.startswith("cuda:"):
        cuda_ids.append(device.split(":", 1)[1])
    elif lower.startswith("gpu:"):
        cuda_ids.append(device.split(":", 1)[1])
    elif lower.isdigit():
        cuda_ids.append(device)

use_mps = use_mps and not cuda_ids

print(json.dumps({
    "exp_name": states.get("exp_name", "exp_0"),
    "project_root": str(project_root.resolve()),
    "command": command,
    "extra_args": extra_args,
    "devices": normalized_devices,
    "cuda_visible_devices": ",".join(cuda_ids),
    "use_mps": use_mps,
}, ensure_ascii=False))
PY
)"
    EXP_NAME="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["exp_name"])' "$METADATA")"
    PROJECT_ROOT="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["project_root"])' "$METADATA")"
    COMMAND="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["command"])' "$METADATA")"
    EXTRA_ARGS="$(python3 -c 'import json,shlex,sys; print(" ".join(shlex.quote(str(x)) for x in json.loads(sys.argv[1])["extra_args"]))' "$METADATA")"
    TRAINING_DEVICES="$(python3 -c 'import json,shlex,sys; print(" ".join(shlex.quote(str(x)) for x in json.loads(sys.argv[1])["devices"]))' "$METADATA")"
    AUTORESEARCH_DEVICES="$(python3 -c 'import json,sys; print(",".join(str(x) for x in json.loads(sys.argv[1])["devices"]))' "$METADATA")"
    CUDA_VISIBLE_DEVICES_VALUE="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["cuda_visible_devices"])' "$METADATA")"
    USE_MPS="$(python3 -c 'import json,sys; print("1" if json.loads(sys.argv[1])["use_mps"] else "0")' "$METADATA")"
else
    PROJECT_ROOT="$RUNTIME_ROOT"
    EXTRA_ARGS=""
    TRAINING_DEVICES="mps"
    AUTORESEARCH_DEVICES="mps"
    CUDA_VISIBLE_DEVICES_VALUE=""
    USE_MPS="1"
fi

PROJECT_ROOT_SHELL="$(python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$PROJECT_ROOT")"
COMMAND_SHELL="$(python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$COMMAND")"
AUTORESEARCH_DEVICES_SHELL="$(python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$AUTORESEARCH_DEVICES")"
CUDA_VISIBLE_DEVICES_SHELL="$(python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$CUDA_VISIBLE_DEVICES_VALUE")"

LAUNCH_DIR="$PROJECT_ROOT/launchscripts"
mkdir -p "$LAUNCH_DIR"

LAUNCH_SCRIPT="$LAUNCH_DIR/launch_${EXP_NAME}.sh"

cat > "$LAUNCH_SCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail

# Launch script for: $EXP_NAME
# Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)

PROJECT_ROOT=$PROJECT_ROOT_SHELL
RAW_COMMAND=$COMMAND_SHELL
EXTRA_ARGS=($EXTRA_ARGS)
TRAINING_DEVICES=($TRAINING_DEVICES)

export AUTORESEARCH_DEVICES=$AUTORESEARCH_DEVICES_SHELL

if [[ "$USE_MPS" == "1" ]]; then
    export CUDA_VISIBLE_DEVICES=""
    export PYTORCH_ENABLE_MPS_FALLBACK="\${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
else
    export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES_SHELL
fi

cd "\$PROJECT_ROOT"

# 将 objective.command 作为完整 shell command 解析
# 例如：
#   RAW_COMMAND="python train.py"
#   FINAL_COMMAND=(python train.py --num_training_steps 10000 --eval_n_steps 1000)
read -r -a BASE_COMMAND <<< "\$RAW_COMMAND"
FINAL_COMMAND=("\${BASE_COMMAND[@]}" "\${EXTRA_ARGS[@]}")

echo "[launch] project_root=\$PROJECT_ROOT"
echo "[launch] command=\${FINAL_COMMAND[*]}"
echo "[launch] AUTORESEARCH_DEVICES=\$AUTORESEARCH_DEVICES"
echo "[launch] CUDA_VISIBLE_DEVICES=\${CUDA_VISIBLE_DEVICES:-}"

exec "\${FINAL_COMMAND[@]}"
EOF

chmod +x "$LAUNCH_SCRIPT"
echo "$LAUNCH_SCRIPT"