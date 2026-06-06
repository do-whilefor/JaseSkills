#!/usr/bin/env python3
from __future__ import annotations
import argparse
from _quality_core import unified, write_report
if __name__ == '__main__':
    ap=argparse.ArgumentParser(description='Run scope, redaction, evidence, anti-hallucination and coverage gates.')
    ap.add_argument('--input', required=True, help='Authorized local project root')
    ap.add_argument('--scope')
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output','-o', default='-')
    a=ap.parse_args(); raise SystemExit(write_report(unified(a.input,a.scope,a.manifest), a.output))
