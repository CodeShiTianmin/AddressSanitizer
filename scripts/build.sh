#!/usr/bin/env bash
# Build one benchmark in one build configuration.
# usage: scripts/build.sh <benchmark> <config>      (configs: see config/build_configs.sh)
# Output: build/<config>/<benchmark>/bin/  (+ build.log)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BENCH="$1"; CONFIG="$2"
source "$ROOT/config/build_configs.sh"
set_build_config "$CONFIG"
export CC="${CC:-clang}" CXX="${CXX:-clang++}"
export DL="$ROOT/downloads" JOBS="${JOBS:-$(nproc)}"
export BUILD_DIR="$ROOT/build/$CONFIG/$BENCH"
export WORK="$BUILD_DIR/work" BIN="$BUILD_DIR/bin"
# Configure scripts run freshly built test programs; leaks there are irrelevant.
export ASAN_OPTIONS="detect_leaks=0"
rm -rf "$BUILD_DIR"; mkdir -p "$WORK" "$BIN"
echo "[build] $BENCH/$CONFIG  CFLAGS='$CFLAGS' LDFLAGS='$LDFLAGS'"
if ! ( cd "$WORK" && bash "$ROOT/benchmarks/$BENCH/build.sh" ) > "$BUILD_DIR/build.log" 2>&1; then
  echo "[build] FAILED: $BENCH/$CONFIG (see $BUILD_DIR/build.log)"; tail -20 "$BUILD_DIR/build.log"; exit 1
fi
rm -rf "$WORK"   # keep only the binaries and the log
ls "$BIN"
