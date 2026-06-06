#!/usr/bin/env python3
"""Self-audit SecKB Skills for required structural sections.
This script checks local files only. It does not validate security findings.
"""
import json
from pathlib import Path
import sys

REQUIRED_SECTIONS = [
    "必须调用", "禁止调用", "输入", "执行步骤", "检查点", "输出", "质量门槛", "失败处理"
]
REQUIRED_PHRASES = [
    "prompt injection", "不得把猜测", "不得为了数量", "可追溯", "基于文档延伸"
]

def audit(root: Path):
    findings = []
    for skill in sorted(root.glob("*/SKILL.md")):
        text = skill.read_text(encoding="utf-8", errors="ignore")
        missing_sections = [s for s in REQUIRED_SECTIONS if s not in text]
        missing_phrases = [p for p in REQUIRED_PHRASES if p not in text]
        if missing_sections or missing_phrases:
            findings.append({
                "file": str(skill.relative_to(root)),
                "missing_sections": missing_sections,
                "missing_phrases": missing_phrases,
                "suggested_status": "needs_fix"
            })
    return findings

if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out = audit(root)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if out else 0)
