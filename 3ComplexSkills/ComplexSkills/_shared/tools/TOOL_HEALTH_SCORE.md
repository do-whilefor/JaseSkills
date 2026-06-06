# Tool health score

This packaged file is a neutral placeholder. Do not treat it as proof that parsers, browsers, proxy tools, Node packages, or language runtimes are available on the target workstation.

On Windows, run from the package root:

```powershell
python _shared/tools/tool_health_check.py --write _shared/tools/tool_health_score.json
python tools/runtime_check.py --out _audit_outputs/runtime_readiness.json
```

Promotion rule: missing or degraded parser/browser/proxy runtime blocks full-AST and full-dynamic claims. Candidate-only analysis may still run when optional runtimes are absent.
