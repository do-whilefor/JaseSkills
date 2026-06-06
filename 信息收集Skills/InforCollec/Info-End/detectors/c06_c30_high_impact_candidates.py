#!/usr/bin/env python3
"""C06-C30 high-impact candidate router.

This file intentionally emits needs_review candidates. It does not confirm
vulnerabilities. It maps normalized/source-sink evidence to high-impact review
queues so unsupported matrix entries stop being orphan rules.
"""
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path

RULES = [
  ('C06_RCE', re.compile(r'eval|Function\(|exec\(|spawn\(|child_process|Runtime\.getRuntime|ProcessBuilder', re.I)),
  ('C07_COMMAND_INJECTION', re.compile(r'exec\(|spawn\(|system\(|popen|child_process|ProcessBuilder|Runtime\.getRuntime', re.I)),
  ('C08_TEMPLATE_INJECTION', re.compile(r'render_template|template\(|Handlebars|Mustache|Jinja|Twig|ERB|Velocity|freemarker', re.I)),
  ('C09_DESERIALIZATION', re.compile(r'pickle|deserialize|unserialize|readObject|ObjectInputStream|yaml\.load|Marshal\.load', re.I)),
  ('C10_ARBITRARY_FILE_READ', re.compile(r'readFile|open\(|send_file|download|FileInputStream|fs\.read|path|filename|filepath', re.I)),
  ('C11_ARBITRARY_FILE_WRITE', re.compile(r'writeFile|open\(.+[wa]|upload|save|FileOutputStream|fs\.write|filename|filepath', re.I)),
  ('C12_SSRF', re.compile(r'fetch\(|axios|requests\.|http\.get|curl|webhook|callback|url|uri|avatar|import_url', re.I)),
  ('C13_SQL_INJECTION', re.compile(r'SELECT |INSERT |UPDATE |DELETE |raw\(|query\(|execute\(|sql', re.I)),
  ('C14_NOSQL_INJECTION', re.compile(r'\$where|find\(|aggregate\(|mongodb|mongoose|NoSQL|query_object', re.I)),
  ('C15_GRAPHQL_AUTHZ', re.compile(r'graphql|query |mutation |resolver|Apollo|Relay|urql', re.I)),
  ('C16_WEBSOCKET_AUTHZ', re.compile(r'WebSocket|socket\.io|ws://|wss://|onmessage|emit\(', re.I)),
  ('C17_OAUTH_OIDC_SAML', re.compile(r'oauth|oidc|saml|redirect_uri|callback|state|nonce|assertion', re.I)),
  ('C18_JWT_SESSION', re.compile(r'jwt|session|cookie|csrf|xsrf|refresh_token|access_token', re.I)),
  ('C19_UPLOAD_EXECUTION_CHAIN', re.compile(r'upload|multipart|filename|mime|convert|imagemagick|ffmpeg|processor', re.I)),
  ('C20_PATH_TRAVERSAL', re.compile(r'\.\./|path\.join|resolve\(|filename|filepath|download', re.I)),
  ('C21_OBJECT_STORAGE_AUTHZ', re.compile(r's3|bucket|blob|signedUrl|presigned|object_key|storage', re.I)),
  ('C22_MASS_ASSIGNMENT', re.compile(r'assign\(|update\(|fill\(|permit\(|request\.body|body\)|DTO|schema', re.I)),
  ('C23_BUSINESS_LOGIC', re.compile(r'coupon|refund|order|invoice|balance|transfer|quota|approval', re.I)),
  ('C24_CACHE_POISONING', re.compile(r'cache|cdn|vary|x-forwarded-host|surrogate|etag', re.I)),
  ('C25_REQUEST_SMUGGLING', re.compile(r'transfer-encoding|content-length|proxy|nginx|apache|haproxy', re.I)),
  ('C26_CORS_POSTMESSAGE', re.compile(r'cors|Access-Control-Allow|postMessage|origin|message event', re.I)),
  ('C27_SENSITIVE_TO_ATO', re.compile(r'password|reset|token|secret|api[_-]?key|private_key|session', re.I)),
  ('C28_ASYNC_INDIRECT', re.compile(r'webhook|callback|cron|queue|job|worker|export|import', re.I)),
  ('C29_SUPPLY_CHAIN_CONFIG', re.compile(r'package\.json|lock|dependency|npm|pip|composer|gem|cargo|go\.mod|pom\.xml', re.I)),
  ('C30_JS_HIDDEN_BACKEND_API', re.compile(r'admin|internal|debug|graphql|mutation|/api/', re.I)),
]

def load_jsonl(path):
    for i,line in enumerate(Path(path).read_text(encoding='utf-8', errors='ignore').splitlines(),1):
        if not line.strip(): continue
        try: yield i,json.loads(line)
        except Exception: continue

def text_of(r):
    ev=r.get('evidence') if isinstance(r.get('evidence'),dict) else {}
    return ' '.join(str(x) for x in [r.get('type'), r.get('endpoint'), r.get('source_file'), r.get('candidate_vulnerability'), r.get('sink'), r.get('sink_type'), ev.get('snippet_preview'), ev.get('source_preview'), ev.get('sink_preview')] if x)

def cid(rule, r):
    raw=rule+'|'+str(r.get('source_file'))+'|'+str(r.get('line') or r.get('source_line'))+'|'+str(r.get('endpoint'))
    return 'HC-'+hashlib.sha256(raw.encode()).hexdigest()[:12]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input', action='append', required=True); ap.add_argument('-o','--out',required=True)
    args=ap.parse_args(); out=[]
    for p in args.input:
        for line_no,r in load_jsonl(p):
            hay=text_of(r)
            for rule,rex in RULES:
                if rex.search(hay):
                    out.append({
                      'candidate_id': cid(rule,r), 'type':'high_impact_candidate', 'candidate_vulnerability': rule,
                      'review_status':'needs_review', 'source_file': r.get('source_file') or (r.get('evidence') or {}).get('source_file') or p,
                      'source_line': r.get('source_line') or r.get('line'), 'endpoint': r.get('endpoint'), 'method': r.get('method'),
                      'evidence': {'source_record_type': r.get('type'), 'input_file': p, 'input_line': line_no, 'source_file': r.get('source_file'), 'source_line': r.get('line') or r.get('source_line'), 'snippet_hash': ((r.get('evidence') if isinstance(r.get('evidence'),dict) else {}) or {}).get('snippet_hash')},
                      'limitation':'heuristic high-impact routing only; requires AST/dataflow/auth/tenant/runtime validation before reportability',
                      'quality_gate': {'required_before_promotion':['source_sink_trace','auth_context','tenant_context','runtime_validation','manifest_linkage']},
                      'report_template':'templates/finding-detail.md'
                    })
                    break
    Path(args.out).write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in out)+('\n' if out else ''), encoding='utf-8')
    print(f'wrote {len(out)} C06-C30 high impact candidates')
if __name__=='__main__': main()
