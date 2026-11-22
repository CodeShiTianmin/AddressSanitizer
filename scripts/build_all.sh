#!/usr/bin/env bash
# Build every benchmark (benchmarks/*/) in every build configuration.
# usage: scripts/build_all.sh [config ...]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/config/build_configs.sh"
CONFIGS="${*:-$BUILD_CONFIGS}"
for c in $CONFIGS; do
  for b in $(ls "$ROOT/benchmarks"); do
    if [ -n "$(ls -A "$ROOT/build/$c/$b/bin" 2>/dev/null)" ] && [ "${FORCE:-0}" = 0 ]; then echo "[build] $b/$c up to date"; continue; fi
    "$ROOT/scripts/build.sh" "$b" "$c"
  done
done
