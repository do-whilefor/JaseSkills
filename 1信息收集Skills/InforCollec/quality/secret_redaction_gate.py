#!/usr/bin/env python3
from __future__ import annotations
import argparse
from _quality_core import redaction_gate, write_report
if __name__ == '__main__':
    ap=argparse.ArgumentParser(description='Fail when evidence contains unredacted secret-like values.')
    ap.add_argument('--input', required=True, help='Evidence manifest JSON'); ap.add_argument('--output','-o', default='-')
    a=ap.parse_args(); raise SystemExit(write_report(redaction_gate(a.input), a.output))
