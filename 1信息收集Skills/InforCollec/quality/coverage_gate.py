#!/usr/bin/env python3
from __future__ import annotations
import argparse
from _quality_core import coverage_gate, write_report
if __name__ == '__main__':
    ap=argparse.ArgumentParser(description='Report coverage counts and detailed skipped-file reasons.')
    ap.add_argument('--input', required=True, help='Evidence manifest JSON')
    ap.add_argument('--project-root', help='Optional authorized project root for skipped-file inventory')
    ap.add_argument('--scope')
    ap.add_argument('--output','-o', default='-')
    a=ap.parse_args(); raise SystemExit(write_report(coverage_gate(a.input, a.project_root, a.scope), a.output))
