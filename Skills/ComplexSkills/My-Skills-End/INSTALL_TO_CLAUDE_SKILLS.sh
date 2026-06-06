#!/usr/bin/env bash
set -euo pipefail
CLAUDE_SKILLS_DIR="${1:-$HOME/.claude/skills}"
SKILL_NAME="${2:-authorized-security-audit-system}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="$CLAUDE_SKILLS_DIR/$SKILL_NAME"

[ -f "$ROOT/SKILL.md" ] || { echo "Root SKILL.md not found: $ROOT" >&2; exit 2; }
[ -d "$ROOT/_shared" ] || { echo "_shared directory not found: $ROOT" >&2; exit 2; }
[ -d "$ROOT/skills" ] || { echo "skills directory not found: $ROOT" >&2; exit 2; }

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "DRY-RUN single-skill install $ROOT -> $TARGET"
  echo "This preserves SKILL.md, _shared, skills, templates, tests, dashboard, quality gate, and scripts together."
  exit 0
fi

mkdir -p "$CLAUDE_SKILLS_DIR"
if [ -e "$TARGET" ]; then
  mv "$TARGET" "$TARGET.backup_$(date +%Y%m%d_%H%M%S)"
fi
cp -R "$ROOT" "$TARGET"
echo "Installed single skill directory: $TARGET"

if [ "${RUN_SELFTEST:-0}" = "1" ]; then
  (cd "$TARGET" && python _shared/selftest/verify_system_integrity.py)
fi
