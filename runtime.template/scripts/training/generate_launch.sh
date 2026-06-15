#!/usr/bin/env bash
set -euo pipefail

# generate_launch.sh - 生成训练 launch script
#
# 输出:
#   <project_root>/launchscripts/launch_<exp_name>.sh
#
# 用法:
#   generate_launch.sh [runtime_root]
#   generate_launch.sh <runtime_root> <exp_name> <training_script_path>
#
# 说明:
#   objective.command 应该是训练脚本路径，例如：
#     "train.py"
#     "scripts/train.py"
#     "train.sh"
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

training_script = objective["command"]

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
    "training_script": training_script,
    "extra_args": extra_args,
    "devices": normalized_devices,
    "cuda_visible_devices": ",".join(cuda_ids),
    "use_mps": use_mps,
}, ensure_ascii=False))
PY
)"
    EXP_NAME="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["exp_name"])' "$METADATA")"
    PROJECT_ROOT="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["project_root"])' "$METADATA")"
    TRAINING_SCRIPT="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["training_script"])' "$METADATA")"
    EXTRA_ARGS="$(python3 -c 'import json,shlex,sys; print(" ".join(shlex.quote(str(x)) for x in json.loads(sys.argv[1])["extra_args"]))' "$METADATA")"
    TRAINING_DEVICES="$(python3 -c 'import json,shlex,sys; print(" ".join(shlex.quote(str(x)) for x in json.loads(sys.argv[1])["devices"]))' "$METADATA")"
    AUTORESEARCH_DEVICES="$(python3 -c 'import json,sys; print(",".join(str(x) for x in json.loads(sys.argv[1])["devices"]))' "$METADATA")"
    CUDA_VISIBLE_DEVICES_VALUE="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["cuda_visible_devices"])' "$METADATA")"
    USE_MPS="$(python3 -c 'import json,sys; print("1" if json.loads(sys.argv[1])["use_mps"] else "0")' "$METADATA")"
else
    PROJECT_ROOT="$RUNTIME_ROOT"
    TRAINING_SCRIPT="$COMMAND"
    EXTRA_ARGS=""
    TRAINING_DEVICES="mps"
    AUTORESEARCH_DEVICES="mps"
    CUDA_VISIBLE_DEVICES_VALUE=""
    USE_MPS="1"
fi

PROJECT_ROOT_SHELL="$(python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$PROJECT_ROOT")"
TRAINING_SCRIPT_SHELL="$(python3 -c 'import shlex,sys; print(shlex.quote(sys.argv[1]))' "$TRAINING_SCRIPT")"
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
TRAINING_SCRIPT=$TRAINING_SCRIPT_SHELL
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

if [[ "\$TRAINING_SCRIPT" = /* ]]; then
    SCRIPT_PATH="\$TRAINING_SCRIPT"
else
    SCRIPT_PATH="\$PROJECT_ROOT/\$TRAINING_SCRIPT"
fi

if [[ ! -f "\$SCRIPT_PATH" ]]; then
    echo "错误: 训练脚本不存在: \$SCRIPT_PATH" >&2
    exit 1
fi

case "\$SCRIPT_PATH" in
    *.py)
        VENV_PY="\$(cd "\$PROJECT_ROOT/../.." && echo "\$(pwd)/.venv/bin/python")"
        if [[ -x "\$VENV_PY" ]]; then
            PYTHON="\$VENV_PY"
        else
            PYTHON="\$(command -v python3)"
        fi
        FINAL_COMMAND=("\$PYTHON" "\$SCRIPT_PATH" "\${EXTRA_ARGS[@]}")
        ;;
    *.sh)
        FINAL_COMMAND=(bash "\$SCRIPT_PATH" "\${EXTRA_ARGS[@]}")
        ;;
    *)
        if [[ -x "\$SCRIPT_PATH" ]]; then
            FINAL_COMMAND=("\$SCRIPT_PATH" "\${EXTRA_ARGS[@]}")
        else
            FINAL_COMMAND=(bash "\$SCRIPT_PATH" "\${EXTRA_ARGS[@]}")
        fi
        ;;
esac

echo "[launch] project_root=\$PROJECT_ROOT"
echo "[launch] training_script=\$SCRIPT_PATH"
echo "[launch] command=\${FINAL_COMMAND[*]}"
echo "[launch] AUTORESEARCH_DEVICES=\$AUTORESEARCH_DEVICES"
echo "[launch] CUDA_VISIBLE_DEVICES=\${CUDA_VISIBLE_DEVICES:-}"

exec "\${FINAL_COMMAND[@]}"
EOF

chmod +x "$LAUNCH_SCRIPT"
echo "$LAUNCH_SCRIPT"
