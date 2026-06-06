#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
raise SystemExit(subprocess.call([sys.executable, str(ROOT/'tools/selftest.py')]))
