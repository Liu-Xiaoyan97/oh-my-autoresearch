#!/usr/bin/env bash
set -euo pipefail

# Install/repair the research-runtime workspace from the oh-my-autoresearch
# submodule, using the manifest installer (the single source of truth).
# copy_if_missing semantics: existing files are preserved. To refresh a
# manifest-installed file after an upstream change, delete it first, then re-run.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW_DIR="$ROOT_DIR/workflow/oh-my-autoresearch"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then PYTHON_BIN="$(command -v python3 || true)"; fi

cd "$ROOT_DIR"

if [ ! -d "$WORKFLOW_DIR/scripts" ]; then
  echo "Missing workflow submodule: $WORKFLOW_DIR"
  echo "Run: git submodule update --init --recursive"
  exit 1
fi
if [ -z "${PYTHON_BIN:-}" ]; then
  echo "Python not found. Expected .venv/bin/python or python3."
  exit 1
fi

exec "$PYTHON_BIN" "$WORKFLOW_DIR/scripts/install_runtime.py" \
  --root "$ROOT_DIR" --workflow-root "$WORKFLOW_DIR"
