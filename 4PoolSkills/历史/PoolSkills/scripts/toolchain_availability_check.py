#!/usr/bin/env python3
import argparse,json,shutil,socket,importlib.util,subprocess,os
from pathlib import Path
def cmd(c): return shutil.which(c) is not None
def mod(m): return importlib.util.find_spec(m) is not None
def port(h,p):
    try: s=socket.create_connection((h,p),timeout=.3); s.close(); return True
    except OSError: return False
def nodepkg(p):
    if not cmd('node'): return False
    return subprocess.run(['node','-e',f"require.resolve('{p}')"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
def chromium_path():
    env=os.environ.get('CHROMIUM_EXECUTABLE') or os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
    if env and Path(env).exists(): return env
    for c in ['chromium','chromium-browser','google-chrome','google-chrome-stable']:
        p=shutil.which(c)
        if p: return p
    return None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--out',default='outputs/tool_availability.json'); a=ap.parse_args(); r=Path(a.root)
    chromium=chromium_path()
    out={'commands':{c:cmd(c) for c in ['git','rg','node','npm','npx','python','go','java','ruby','php','docker']},'python_modules':{m:mod(m) for m in ['playwright','jsonschema','yaml','libcst','tree_sitter']},'node_packages':{p:nodepkg(p) for p in ['typescript','@babel/parser','@playwright/test','@playwright/mcp']},'browser':{'system_chromium_path':chromium,'launch_supported_by_package':'scripts/browser_role_tenant_matrix_replay.py uses system Chromium executable when Playwright bundled browsers are unavailable'},'ports':{'burp_127_0_0_1_8080':port('127.0.0.1',8080)},'paths':{'har_dir':(r/'evidence'/'har').exists(),'mcp_config':any((r/x).exists() for x in ['.mcp.json','.claude/settings.json'])},'policy':{'missing_tool_max_status':'needs_review','tool_alert_only_can_confirm':False}}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
