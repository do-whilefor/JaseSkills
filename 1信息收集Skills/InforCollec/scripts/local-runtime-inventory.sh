#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
OUT="${2:-runtime-inventory.md}"

{
  echo "# Local Runtime Inventory"
  echo
  echo "## Project Root"
  printf '%s\n' "$ROOT"
  echo
  echo "## Runtime Files"
  find "$ROOT" -maxdepth 3 -type f \( \
    -name 'docker-compose.yml' -o -name 'compose.yml' -o -name 'package.json' -o \
    -name 'pyproject.toml' -o -name 'requirements.txt' -o -name 'pom.xml' -o \
    -name 'build.gradle' -o -name 'go.mod' -o -name 'Cargo.toml' -o -name 'Makefile' -o \
    -name 'Dockerfile' -o -name 'nginx.conf' -o -name 'Caddyfile' \
  \) -print 2>/dev/null | sed 's/^/- /'
  echo
  echo "## Listening Ports: ss -lntup"
  if command -v ss >/dev/null 2>&1; then ss -lntup 2>/dev/null || true; else echo "ss not found"; fi
  echo
  echo "## lsof -i"
  if command -v lsof >/dev/null 2>&1; then lsof -i -P -n 2>/dev/null || true; else echo "lsof not found"; fi
  echo
  echo "## docker ps"
  if command -v docker >/dev/null 2>&1; then docker ps 2>/dev/null || true; else echo "docker not found"; fi
  echo
  echo "## docker compose ps"
  if command -v docker >/dev/null 2>&1; then docker compose ps 2>/dev/null || true; else echo "docker not found"; fi
} > "$OUT"

echo "Wrote $OUT"
