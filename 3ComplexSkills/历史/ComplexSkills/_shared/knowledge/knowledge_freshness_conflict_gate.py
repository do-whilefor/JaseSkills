#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, datetime as dt
from pathlib import Path
MAX_AGE_DAYS=180
def validate(manifest: dict) -> dict:
    errors=[]; warnings=[]; today=dt.date.today()
    for i,ref in enumerate(manifest.get('knowledge_references') or []):
        if ref.get('used_as_evidence') is True or ref.get('role') in {'vulnerability_evidence','dynamic_evidence','code_evidence'}:
            errors.append(f'knowledge_references[{i}] cannot be used as direct evidence')
        date=ref.get('source_date') or ref.get('last_reviewed')
        if date:
            try:
                age=(today-dt.date.fromisoformat(str(date)[:10])).days
                if age>MAX_AGE_DAYS and ref.get('freshness_reviewed') is not True: errors.append(f'knowledge_references[{i}] stale without freshness_reviewed=true')
            except Exception: warnings.append(f'knowledge_references[{i}] unparseable date')
        if ref.get('conflict') is True and manifest.get('final_status')=='confirmed': errors.append(f'knowledge_references[{i}] conflict cannot be confirmed')
    return {'passed':not errors,'errors':errors,'warnings':warnings}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest')
    a=ap.parse_args(); print(json.dumps(validate(json.loads(Path(a.manifest).read_text(encoding='utf-8'))),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
