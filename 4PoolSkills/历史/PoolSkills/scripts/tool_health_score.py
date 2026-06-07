#!/usr/bin/env python3
import json, os, shutil, socket, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQ = json.loads((ROOT/'config/tool_health_requirements.json').read_text(encoding='utf-8'))

def run(cmd, timeout=5):
    try:
        p=subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        return p.returncode==0, (p.stdout+p.stderr).strip()[:500]
    except Exception as e:
        return False, str(e)

def tcp(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, 'tcp open'
    except Exception as e:
        return False, str(e)

checks={
 'python_runtime': lambda: run('python --version || python3 --version'),
 'node_runtime': lambda: run('node --version'),
 'java_runtime': lambda: run('java -version'),
 'php_runtime': lambda: run('php -v'),
 'go_runtime': lambda: run('go version'),
 'rust_runtime': lambda: run('cargo --version'),
 'playwright': lambda: run('python -m playwright --version || npx playwright --version'),
 'browser': lambda: (False, 'manual_required: run playwright install/check in local environment'),
 'burp_proxy': lambda: tcp('127.0.0.1', 8080),
 'mcp': lambda: (False, 'manual_required: MCP availability must be checked by Claude host'),
 'babel': lambda: run('node -e "require(\'@babel/parser\'); console.log(\'ok\')"'),
 'typescript_compiler_api': lambda: run('node -e "require(\'typescript\'); console.log(\'ok\')"'),
 'tree_sitter': lambda: run('python -c "import tree_sitter; print(\'ok\')" || tree-sitter --version'),
 'python_ast_libcst': lambda: run('python -c "import ast; import libcst; print(\'ok\')"'),
 'javaparser': lambda: (False, 'manual_required: check JavaParser jar/package in local classpath'),
 'php_parser': lambda: run('php -r "include \"vendor/autoload.php\"; echo class_exists(\"PhpParser\\\\ParserFactory\") ? \"ok\" : \"missing\";"'),
 'ruby_ripper': lambda: run('ruby -rripper -e "puts :ok"'),
 'route_extractor': lambda: run(f'python "{ROOT}/scripts/route_extractor.py" --self-test'),
 'evidence_manifest_write': lambda: _write_check(),
 'dashboard_generator': lambda: run(f'python "{ROOT}/scripts/dashboard_status_generator.py" --self-test'),
 'regression_runner': lambda: run(f'python "{ROOT}/scripts/adversarial_regression_runner.py" --self-test')
}

def _write_check():
    out=ROOT/'outputs'; out.mkdir(exist_ok=True)
    p=out/'_write_check.tmp'
    try:
        p.write_text('ok', encoding='utf-8'); p.unlink()
        return True, 'write ok'
    except Exception as e:
        return False, str(e)

def main():
    results=[]; score=0
    for item in REQ:
        fn=checks.get(item['id'], lambda:(False,'no check implemented'))
        ok,msg=fn()
        if ok:
            status='ready'; points=5
        elif 'manual_required' in msg:
            status='manual_required'; points=1
        elif 'missing' in msg.lower() or 'not found' in msg.lower():
            status='missing'; points=0
        else:
            status='degraded'; points=2
        score += points
        results.append({**item, 'status':status, 'message':msg})
    max_score=len(REQ)*5
    summary={'status':'ready' if score==max_score else 'degraded', 'score':score, 'max_score':max_score, 'items':results}
    out=ROOT/'outputs/tool_health_score.json'; out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
