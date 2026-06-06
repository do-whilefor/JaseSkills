#!/usr/bin/env python3
"""Heuristic source→sink dataflow candidate builder for authorized local code review.

This is deliberately conservative: outputs candidates with review_status=needs_review.
It never performs exploitation and never confirms vulnerabilities.
"""
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path

SKIP = {'.git','node_modules','dist','build','.next','.nuxt','coverage','__pycache__'}
SOURCE_RE = re.compile(r"\b(req\.(?:query|params|body|headers|cookies)|request\.(?:args|form|json|files|headers|cookies)|params\[|query\[|localStorage|getItem\(|URLSearchParams|location\.|postMessage|process\.env)", re.I)
SINKS = {
    'command_execution': re.compile(r"\b(exec|spawn|system|popen|subprocess\.|child_process\.|os\.system)\b", re.I),
    'file_read_write': re.compile(r"\b(readFile|writeFile|open\(|createReadStream|createWriteStream|send_file|File\(|Path\()", re.I),
    'template_render': re.compile(r"\b(render_template|render\(|compileTemplate|Handlebars\.compile|pug\.render|ejs\.render)", re.I),
    'sql_query': re.compile(r"\b(query\(|execute\(|raw\(|sequelize\.query|createQueryBuilder)", re.I),
    'nosql_query': re.compile(r"\b(findOne\(|find\(|updateOne\(|deleteOne\(|aggregate\()", re.I),
    'ssrf_url_fetch': re.compile(r"\b(requests\.|urllib\.|axios\.|fetch\(|http\.get|http\.request|curl\()", re.I),
    'redirect': re.compile(r"\b(redirect\(|res\.redirect|window\.location|location\.href)", re.I),
    'dom_sink': re.compile(r"\b(innerHTML|outerHTML|insertAdjacentHTML|dangerouslySetInnerHTML|eval\(|Function\()", re.I),
}
TENANT_RE = re.compile(r"tenant|orgId|organization|workspace|accountId|projectId|ownerId", re.I)
AUTH_RE = re.compile(r"auth|jwt|session|permission|role|guard|policy|csrf|login_required|require_user|isAuthenticated|authorize", re.I)

def walk(root: Path):
    for p in root.rglob('*'):
        if any(part in SKIP for part in p.parts): continue
        if p.is_file() and p.suffix.lower() in {'.py','.js','.ts','.tsx','.jsx','.java','.php','.go','.rs','.rb'}:
            yield p

def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]

def scan_file(path: Path, root: Path):
    rel = str(path.relative_to(root)).replace('\\','/')
    lines = path.read_text(errors='ignore').splitlines()
    source_lines = [(i+1, line) for i, line in enumerate(lines) if SOURCE_RE.search(line)]
    findings = []
    for sline, stext in source_lines:
        window_start = max(1, sline - 12)
        window_end = min(len(lines), sline + 18)
        window = '\n'.join(lines[window_start-1:window_end])
        for sink_type, rx in SINKS.items():
            if rx.search(window):
                auth = bool(AUTH_RE.search(window))
                tenant = bool(TENANT_RE.search(window))
                finding_type = {
                    'command_execution':'command_injection_candidate',
                    'file_read_write':'arbitrary_file_access_candidate',
                    'template_render':'template_injection_candidate',
                    'sql_query':'sql_injection_candidate',
                    'nosql_query':'nosql_injection_candidate',
                    'ssrf_url_fetch':'ssrf_candidate',
                    'redirect':'open_redirect_candidate',
                    'dom_sink':'dom_xss_candidate',
                }[sink_type]
                findings.append({
                    'type':'source_sink_dataflow_candidate',
                    'candidate_vulnerability': finding_type,
                    'source_file': rel,
                    'source_line': sline,
                    'sink_type': sink_type,
                    'window_start_line': window_start,
                    'window_end_line': window_end,
                    'auth_context_present': auth,
                    'tenant_context_present': tenant,
                    'confidence': 0.45 if not auth else 0.55,
                    'review_status': 'needs_review',
                    'evidence': {'window_hash': sha(window), 'source_preview': stext.strip()[:220], 'window_preview': ' '.join(window.split())[:260]},
                    'limitation': 'heuristic window-based dataflow; requires parser-backed confirmation before reporting'
                })
    return findings

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('-o','--out',default='-')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    findings=[]
    for p in walk(root): findings.extend(scan_file(p, root))
    data=''.join(json.dumps(x, ensure_ascii=False)+'\n' for x in findings)
    if args.out=='-': print(data,end='')
    else: Path(args.out).write_text(data,encoding='utf-8')
    print(f"wrote {len(findings)} source-sink candidates", file=__import__('sys').stderr)
if __name__=='__main__': main()
