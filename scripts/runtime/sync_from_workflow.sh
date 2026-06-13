#!/usr/bin/env bash
set -euo pipefail

# Update the workflow submodule, then (re)install the runtime via the manifest.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

git submodule update --init --recursive workflow/oh-my-autoresearch

exec "$ROOT_DIR/scripts/bootstrap.sh"
