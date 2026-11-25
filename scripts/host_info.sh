#!/usr/bin/env bash
# Host-side facts that are invisible from inside the container (appended to results/env.txt).
echo "host_os:     $(. /etc/os-release; echo "$PRETTY_NAME") (docker host)"
echo "docker:      $(docker --version 2>/dev/null || echo n/a)"
echo "image:       ${IMAGE:-asan-repl:1.0} ($(docker inspect --format '{{.Id}}' "${IMAGE:-asan-repl:1.0}" 2>/dev/null | cut -c1-19))"
