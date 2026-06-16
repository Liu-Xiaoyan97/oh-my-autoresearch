#!/usr/bin/env bash
set -euo pipefail

# generate_remote.sh - 生成「远程训练三件套」脚本（generate_launch.sh 的远程版）
#
# 读取 objective.json 的 hosts/project_root/command/num_training_steps/eval_n_steps，
# 在 <project_root>/launchscripts/ 下生成：
#   copy_to_remote.sh         本地 project_root/ → 第一个 host:~/<basename>/ (rsync --delete 覆盖)
#   train_on_remote.sh [exp]  链式 SSH(ProxyJump) 登录到最后一个 host，cd 工作目录，nohup 挂起训练，回显远程 PID
#   query_from_remote.sh [exp] 登录第一个 host，取回训练日志到本地并用 monitor_training.py 解析为 training-progress JSON
#
# hosts 共享文件系统：上传到第一个 host 即对最后一个 host 可见；日志由最后一个 host 写、第一个 host 读。
# 远端解释器优先级：project 自身 uv 环境(uv run，需 pyproject.toml) > .venv/bin/python > python3。
# hosts 每项可为字符串(SSH 别名，如 "mgt")或对象({"host","user","port","keyPath"})；
# 端口/密钥建议写进 ~/.ssh/config，本生成器只处理 别名 / user@host。
#
# 用法: generate_remote.sh [runtime_root]

RUNTIME_ROOT="${1:-runtime}"

META="$(python3 - "$RUNTIME_ROOT" <<'PY'
import json, sys, shlex
from pathlib import Path

runtime_root = Path(sys.argv[1]).resolve()
host_root = runtime_root.parent
objective = json.loads((runtime_root / "states" / "objective.json").read_text(encoding="utf-8"))
states = json.loads((runtime_root / "states" / "states.json").read_text(encoding="utf-8"))

hosts = objective.get("hosts", []) or []

def dest(h):
    if isinstance(h, str):
        return h.strip()
    host = str(h.get("host", "")).strip()
    user = str(h.get("user", "")).strip()
    return f"{user}@{host}" if user else host

dests = [d for d in (dest(h) for h in hosts) if d]
if not dests:
    print(json.dumps({"error": "objective.hosts 为空或无效"}))
    sys.exit(0)

first = dests[0]
last = dests[-1]
jump = ",".join(dests[:-1])  # 中间跳板（不含最后一个），供 ssh -J 使用

project_root = Path(objective.get("project_root", "."))
if not project_root.is_absolute():
    project_root = host_root / project_root
project_root = project_root.resolve()
basename = project_root.name

command = objective.get("command", "train.py")
num_steps = objective.get("num_training_steps")
eval_steps = objective.get("eval_n_steps")
extra = []
if num_steps is not None:
    extra += ["--num_training_steps", str(num_steps)]
if eval_steps is not None:
    extra += ["--eval_n_steps", str(eval_steps)]
extra_args = " ".join(shlex.quote(x) for x in extra)

devices = [str(d).strip() for d in (objective.get("devices") or []) if str(d).strip()]
cuda_ids = []
for d in devices:
    low = d.lower()
    if low.startswith("cuda:") or low.startswith("gpu:"):
        cuda_ids.append(d.split(":", 1)[1])
    elif low.isdigit():
        cuda_ids.append(d)
env_prefix = ""
if devices:
    env_prefix += "export AUTORESEARCH_DEVICES=" + shlex.quote(",".join(devices)) + "; "
if cuda_ids:
    env_prefix += "export CUDA_VISIBLE_DEVICES=" + shlex.quote(",".join(cuda_ids)) + "; "

env_prefix += "export HF_HUB_OFFLINE=1; "
env_prefix += "export TRANSFORMERS_OFFLINE=1; "

print(json.dumps({
    "first": first, "last": last, "jump": jump,
    "project_root": str(project_root), "basename": basename,
    "command": command, "extra_args": extra_args,
    "exp_name": states.get("exp_name", "exp_0"),
    "runtime_root": str(runtime_root),
    "env_prefix": env_prefix,
}, ensure_ascii=False))
PY
)"

ERR="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("error",""))' "$META")"
if [[ -n "$ERR" ]]; then
    echo "错误: $ERR" >&2
    exit 1
fi

get() { python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get(sys.argv[2],""))' "$META" "$1"; }

FIRST="$(get first)"
LAST="$(get last)"
JUMP="$(get jump)"
PROJECT_ROOT="$(get project_root)"
BASENAME="$(get basename)"
COMMAND="$(get command)"
EXTRA_ARGS="$(get extra_args)"
EXP_NAME="$(get exp_name)"
RUNTIME_ROOT_ABS="$(get runtime_root)"
ENV_PREFIX="$(get env_prefix)"

JUMP_OPT=""
if [[ -n "$JUMP" ]]; then
    JUMP_OPT="-J $JUMP"
fi

LAUNCH_DIR="$PROJECT_ROOT/launchscripts"
mkdir -p "$LAUNCH_DIR"

COPY="$LAUNCH_DIR/copy_to_remote.sh"
TRAIN="$LAUNCH_DIR/train_on_remote.sh"
QUERY="$LAUNCH_DIR/query_from_remote.sh"

GEN_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ---------- copy_to_remote.sh ----------
cat > "$COPY" <<EOF
#!/usr/bin/env bash
set -euo pipefail
# 生成于 $GEN_AT by generate_remote.sh —— 本地代码覆盖上传到远端第一个 host（共享文件系统）
FIRST_DEST=$(printf '%q' "$FIRST")
PROJECT_ROOT=$(printf '%q' "$PROJECT_ROOT")
REMOTE_DIR=$(printf '%q' "$BASENAME")
EOF
cat >> "$COPY" <<'EOF'
echo "→ 上传 $PROJECT_ROOT/ → $FIRST_DEST:~/$REMOTE_DIR/ (rsync --delete 覆盖)" >&2
ssh -o BatchMode=yes "$FIRST_DEST" "mkdir -p $REMOTE_DIR"
rsync -a --whole-file --inplace --exclude='__pycache__/'  --exclude='.venv/' --exclude='uv.lock' --exclude='pyproject.toml' --exclude='.python-version' --exclude='output/' --exclude='launchscripts/' --exclude='runtime'  -e "ssh -T -o Compression=no -o BatchMode=yes" "$PROJECT_ROOT/" "$FIRST_DEST:$REMOTE_DIR/"
echo "✓ copy_to_remote 完成: $FIRST_DEST:~/$REMOTE_DIR" >&2
EOF

# ---------- train_on_remote.sh ----------
cat > "$TRAIN" <<EOF
#!/usr/bin/env bash
set -euo pipefail
# 生成于 $GEN_AT by generate_remote.sh —— 链式登录最后一个 host, nohup 挂起训练, 回显远程 PID
LAST_DEST=$(printf '%q' "$LAST")
JUMP_OPT=$(printf '%q' "$JUMP_OPT")
REMOTE_DIR=$(printf '%q' "$BASENAME")
COMMAND=$(printf '%q' "$COMMAND")
EXTRA_ARGS=$(printf '%q' "$EXTRA_ARGS")
ENV_PREFIX="$ENV_PREFIX"
DEFAULT_EXP=$(printf '%q' "$EXP_NAME")
EOF
cat >> "$TRAIN" <<'EOF'
EXP_NAME="${1:-$DEFAULT_EXP}"
LOG="train-of-${EXP_NAME}.log"
REMOTE_CMD="cd \"\$HOME/$REMOTE_DIR\" && ${ENV_PREFIX}if command -v uv >/dev/null 2>&1 && [ -f pyproject.toml ]; then RUN=\"uv run python\"; elif [ -x .venv/bin/python ]; then RUN=.venv/bin/python; else RUN=\$(command -v python3); fi && nohup \$RUN $COMMAND $EXTRA_ARGS > \"$LOG\" 2>&1 < /dev/null & echo \$!"
echo "→ 链式登录 $LAST_DEST ${JUMP_OPT:+($JUMP_OPT)} 启动训练 exp=$EXP_NAME" >&2
PID=$(ssh -o BatchMode=yes $JUMP_OPT "$LAST_DEST" "$REMOTE_CMD")
echo "$PID"
EOF

# ---------- query_from_remote.sh ----------
cat > "$QUERY" <<EOF
#!/usr/bin/env bash
set -euo pipefail
# 生成于 $GEN_AT by generate_remote.sh —— 登录第一个 host 取回日志并解析为 training-progress JSON
FIRST_DEST=$(printf '%q' "$FIRST")
REMOTE_DIR=$(printf '%q' "$BASENAME")
RUNTIME_ROOT_ABS=$(printf '%q' "$RUNTIME_ROOT_ABS")
DEFAULT_EXP=$(printf '%q' "$EXP_NAME")
EOF
cat >> "$QUERY" <<'EOF'
EXP_NAME="${1:-$DEFAULT_EXP}"
REMOTE_LOG="$REMOTE_DIR/train-of-${EXP_NAME}.log"
LOCAL_LOG_DIR="$RUNTIME_ROOT_ABS/logs"
LOCAL_LOG="$LOCAL_LOG_DIR/train-of-${EXP_NAME}.log"
mkdir -p "$LOCAL_LOG_DIR"
ssh -o BatchMode=yes "$FIRST_DEST" "cat $REMOTE_LOG 2>/dev/null" > "$LOCAL_LOG" || true
python3 "$RUNTIME_ROOT_ABS/scripts/training/monitor_training.py" "$RUNTIME_ROOT_ABS" "$EXP_NAME"
EOF

chmod +x "$COPY" "$TRAIN" "$QUERY"
echo "$COPY"
echo "$TRAIN"
echo "$QUERY"
