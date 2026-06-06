#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, zipfile, tarfile
from pathlib import Path
SENSITIVE=re.compile(r'(token|secret|api[_-]?key|password|passwd|private[_-]?key|session|cookie|database[_-]?url|client[_-]?secret)',re.I)
EMBED_GO=re.compile(r'//go:embed\s+(.+)')
RUST_INCLUDE=re.compile(r'include_(?:str|bytes)!\s*\(\s*["\']([^"\']+)')
SKIP={'.git','node_modules','target','.venv','venv','__pycache__'}
def red(s:str)->str:
    s=str(s)
    s=re.sub(r'(?i)(token|secret|api[_-]?key|password|passwd|client[_-]?secret)([=: ]+)([^,;\s]+)', r'\1\2****', s)
    return (s[:160]+'...') if len(s)>180 else s.replace('\n',' ')
def skip(p:Path)->bool: return any(x in p.parts for x in SKIP)
def inspect_zip(p:Path):
    out=[]
    try:
        with zipfile.ZipFile(p) as z:
            for info in z.infolist()[:2000]:
                name=info.filename
                if SENSITIVE.search(name) or name.endswith(('.env','.pem','.key','.sqlite','.db','.dump','.bak')):
                    out.append({'entry':name,'size':info.file_size,'reason':'sensitive filename or risky extension'})
    except Exception as e: out.append({'error':str(e)})
    return out
def inspect_tar(p:Path):
    out=[]
    try:
        with tarfile.open(p) as t:
            for m in t.getmembers()[:2000]:
                name=m.name
                if SENSITIVE.search(name) or name.endswith(('.env','.pem','.key','.sqlite','.db','.dump','.bak')):
                    out.append({'entry':name,'size':m.size,'reason':'sensitive filename or risky extension'})
    except Exception as e: out.append({'error':str(e)})
    return out
def main():
    ap=argparse.ArgumentParser(description='Read-only package artifact inventory. It does not build, pack, install, or execute project code.')
    ap.add_argument('root'); ap.add_argument('-o','--out',default='package-artifact-inventory.md'); ap.add_argument('--max-files',type=int,default=50000)
    args=ap.parse_args(); root=Path(args.root).resolve(); rows=[]; count=0
    for p in root.rglob('*'):
        if skip(p) or not p.is_file(): continue
        count+=1
        if count>args.max_files: break
        rel=str(p.relative_to(root)); suf=p.suffix.lower()
        if p.name=='package.json':
            try:
                data=json.loads(p.read_text(errors='ignore'))
                rows.append(('PKGJSON',rel,red({'name':data.get('name'),'version':data.get('version'),'files':data.get('files'),'main':data.get('main'),'scripts':list((data.get('scripts') or {}).keys())}),'静态候选；不要执行 npm pack/prepare 脚本'))
            except Exception as e: rows.append(('PKGJSON',rel,red(e),'读取失败'))
        elif p.name in ('pyproject.toml','setup.py','setup.cfg','MANIFEST.in'):
            rows.append(('PY-PACKAGE',rel,'Python package metadata file','检查 wheel/sdist 是否包含敏感文件'))
        elif p.name in ('pom.xml','build.gradle','settings.gradle'):
            rows.append(('JAVA-BUILD',rel,'Java build metadata file','检查 jar/war 产物和资源目录'))
        elif suf in ('.whl','.jar','.war','.zip'):
            for item in inspect_zip(p): rows.append(('ARCHIVE',rel,red(item),'只读 archive 目录候选'))
        elif suf in ('.tar','.gz','.tgz') or p.name.endswith(('.tar.gz','.tar.bz2')):
            for item in inspect_tar(p): rows.append(('ARCHIVE',rel,red(item),'只读 archive 目录候选'))
        elif suf=='.go':
            txt=p.read_text(errors='ignore')[:200000]
            for m in EMBED_GO.finditer(txt): rows.append(('GO-EMBED',rel,red(m.group(1)),'Go embed 候选，需检查运行态是否暴露'))
        elif suf=='.rs':
            txt=p.read_text(errors='ignore')[:200000]
            for m in RUST_INCLUDE.finditer(txt): rows.append(('RUST-INCLUDE',rel,red(m.group(1)),'Rust include 候选，需检查运行态是否暴露'))
    out=['# 包产物只读 Inventory\n','- 声明：只读解析已有文件；不执行 build/install/pack；不运行项目脚本；所有结果都是候选。\n','| 类型 | 文件 | 摘要 | 下一步 |','|---|---|---|---|']
    for r in rows[:1000]: out.append('| `%s` | `%s` | `%s` | %s |'%r)
    if not rows: out.append('| - | - | 未发现包产物候选 | - |')
    Path(args.out).write_text('\n'.join(out),encoding='utf-8'); print(f'Wrote {args.out} ({len(rows)} rows)')
if __name__=='__main__': main()
