#!/usr/bin/env python3
"""Parse local Burp XML/JSON exports into redacted request/response artifacts."""
from __future__ import annotations
import argparse, base64, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from har_redaction_and_hash import convert, ROOT
SECRET_RE=re.compile(r'(authorization|cookie|token|secret|api[-_]?key|password):\s*[^\r\n]+', re.I)
def redact_text(s: str) -> str: return SECRET_RE.sub(lambda m: m.group(1)+': <redacted>', s)
def parse_xml(path: Path) -> dict:
    tree=ET.parse(path); entries=[]
    for item in tree.findall('.//item'):
        req_el=item.find('request'); resp_el=item.find('response')
        def dec(el):
            if el is None or el.text is None: return ''
            txt=el.text.strip()
            if el.get('base64') == 'true':
                try: txt=base64.b64decode(txt).decode('utf-8','ignore')
                except Exception: pass
            return redact_text(txt)
        entries.append({'request':{'raw':dec(req_el)},'response':{'raw':dec(resp_el)}})
    return {'log':{'entries':entries}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('export'); ap.add_argument('--run-id',default='burp-local-run'); ap.add_argument('--out')
    a=ap.parse_args(); p=Path(a.export); tmp=ROOT/'_shared/runs'/a.run_id/'burp_as_har.json'; tmp.parent.mkdir(parents=True,exist_ok=True)
    if p.suffix.lower()=='.xml': obj=parse_xml(p)
    else: obj=json.loads(p.read_text(encoding='utf-8'))
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    groups=convert(tmp, ROOT/'_shared/runs', a.run_id)
    text=json.dumps({'schema_version':'burp_export_dynamic_evidence_v1','groups':groups},ensure_ascii=False,indent=2)
    if a.out: Path(a.out).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()
