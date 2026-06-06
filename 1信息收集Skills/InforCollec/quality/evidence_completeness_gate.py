#!/usr/bin/env python3
from __future__ import annotations
import argparse
from _quality_core import evidence_completeness_gate, write_report
if __name__ == '__main__':
    ap=argparse.ArgumentParser(description='Fail when evidence lacks source, line, hash, reason, reproduction command or limitation.')
    ap.add_argument('--input', required=True); ap.add_argument('--output','-o', default='-')
    a=ap.parse_args(); raise SystemExit(write_report(evidence_completeness_gate(a.input), a.output))
