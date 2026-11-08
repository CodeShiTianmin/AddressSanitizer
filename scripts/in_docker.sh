#!/usr/bin/env bash
# Run a command inside the pinned experiment container with the repository mounted at /work.
# usage: scripts/in_docker.sh <command...>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${IMAGE:-asan-repl:1.0}"
TTY=""; [ -t 0 ] && TTY="-it"
exec docker run --rm $TTY --user "$(id -u):$(id -g)" -e HOME=/tmp -e BENCH_CPU -e JOBS \
     --cap-add SYS_PTRACE -v "$ROOT":/work -w /work "$IMAGE" "$@"
