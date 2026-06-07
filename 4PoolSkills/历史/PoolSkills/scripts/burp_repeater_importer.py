#!/usr/bin/env python3
import base64, json, re, sys, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)
def parse_raw(text):
    first=text.splitlines()[0] if text.splitlines() else ''; m=re.match(r'(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(\S+)', first)
    return {'method':m.group(1) if m else 'UNKNOWN','path':m.group(2) if m else '', 'raw_summary':text[:500]}
def parse(path):
    p=Path(path); text=p.read_text(encoding='utf-8', errors='ignore'); items=[]
    if text.lstrip().startswith('<'):
        root=ET.fromstring(text)
        for item in root.findall('.//item'):
            req=item.findtext('request') or ''; elem=item.find('request'); is_b64=elem is not None and elem.get('base64')=='true'
            if is_b64: req=base64.b64decode(req).decode('utf-8','ignore')
            rec=parse_raw(req); rec.update({'host':item.findtext('host'),'url':item.findtext('url')}); items.append(rec)
    else: items.append(parse_raw(text))
    out={'status':'ok','source':str(p),'items':items,'note':'Imported as evidence candidates only; quality gate still required.'}
    (OUT/'burp_repeater_import.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': parse(sys.argv[1] if len(sys.argv)>1 else ROOT/'tests/fixtures/burp_sample_request.txt')
