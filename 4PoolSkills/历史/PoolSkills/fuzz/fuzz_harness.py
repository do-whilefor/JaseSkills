#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, random, string

def fuzz_parser(func, iterations=100):
    anomalies=[]
    for i in range(iterations):
        s=''.join(random.choice(string.printable) for _ in range(random.randint(0,128)))
        try: func(s)
        except Exception as e: anomalies.append({'iteration':i,'exception':type(e).__name__,'input_len':len(s)})
    return {'schema_version':'fuzz-result-v1','iterations':iterations,'anomalies':anomalies,'policy':'local non-destructive parser fuzz only'}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--iterations',type=int,default=10); ns=ap.parse_args(); print(json.dumps(fuzz_parser(lambda x:x.encode('utf-8'),ns.iterations),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
