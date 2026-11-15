#!/usr/bin/env bash
# Download all third-party sources listed in scripts/sources.txt into downloads/
# and verify their SHA-256 checksums. Idempotent.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DL="${ROOT}/downloads"
mkdir -p "$DL"
grep -v '^#' "$ROOT/scripts/sources.txt" | while read -r name sha url; do
  [ -z "$name" ] && continue
  f="$DL/$name"
  if [ ! -f "$f" ] || ! echo "$sha  $f" | sha256sum -c --status; then
    echo "[fetch] $name"
    curl -fsSL --retry 3 -o "$f.part" "$url"
    mv "$f.part" "$f"
  fi
  echo "$sha  $f" | sha256sum -c --quiet
done
echo "[fetch] all sources present and verified"
