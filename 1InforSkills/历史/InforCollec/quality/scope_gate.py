#!/usr/bin/env python3
from __future__ import annotations
import argparse
from _quality_core import scope_gate, write_report
if __name__ == '__main__':
    ap=argparse.ArgumentParser(description='Fail when input or evidence source files leave authorized scope.')
    ap.add_argument('--input', required=True); ap.add_argument('--scope'); ap.add_argument('--manifest'); ap.add_argument('--output','-o', default='-')
    a=ap.parse_args(); raise SystemExit(write_report(scope_gate(a.input,a.scope,a.manifest), a.output))
