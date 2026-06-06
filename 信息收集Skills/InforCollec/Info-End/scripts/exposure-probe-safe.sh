#!/usr/bin/env bash
set -euo pipefail
BASE=""; PATHS=""; OUT="probe-results.tsv"; REPEAT=2
ALLOW_HOSTS=(); ALLOW_NONLOCAL=0; ACCEPT_VARIANTS=1; SLASH_VARIANTS=1
usage(){ echo "usage: $0 --base http://127.0.0.1:3000 --paths paths.txt [--out probe-results.tsv] [--repeat 2] [--allow-host host] [--no-accept-variants] [--no-slash-variants]" >&2; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE="$2"; shift 2 ;;
    --paths) PATHS="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --repeat) REPEAT="$2"; shift 2 ;;
    --allow-host) ALLOW_HOSTS+=("$2"); shift 2 ;;
    --allow-nonlocal) ALLOW_NONLOCAL=1; shift ;;
    --no-accept-variants) ACCEPT_VARIANTS=0; shift ;;
    --no-slash-variants) SLASH_VARIANTS=0; shift ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done
[[ -n "$BASE" && -n "$PATHS" ]] || usage
[[ -f "$PATHS" ]] || { echo "paths file not found: $PATHS" >&2; exit 2; }
host=$(python3 - <<'PY' "$BASE"
from urllib.parse import urlparse
import sys
print(urlparse(sys.argv[1]).hostname or "")
PY
)
is_local=0
case "$host" in 127.0.0.1|localhost|0.0.0.0|::1) is_local=1 ;; esac
allowed_by_host=0
for h in "${ALLOW_HOSTS[@]:-}"; do [[ "$host" == "$h" ]] && allowed_by_host=1; done
if [[ "$is_local" -ne 1 && "$allowed_by_host" -ne 1 && "$ALLOW_NONLOCAL" -ne 1 ]]; then echo "Refusing non-local base without exact --allow-host or --allow-nonlocal: $BASE" >&2; exit 3; fi
if ! [[ "$REPEAT" =~ ^[0-9]+$ ]] || [[ "$REPEAT" -lt 1 || "$REPEAT" -gt 3 ]]; then echo "Refusing repeat outside 1-3: $REPEAT" >&2; exit 4; fi
redact_cell(){ python3 - <<'PY' "$1"
import re,sys
s=sys.argv[1]
s=re.sub(r'(?i)(token|secret|api[_-]?key|password|session|cookie)=([^&\s]+)', lambda m:m.group(1)+'=****', s)
s=re.sub(r'eyJ[A-Za-z0-9_.-]{20,}', 'eyJ****', s)
print(s)
PY
}
make_variants(){ local p="$1"; printf '%s\n' "$p"; if [[ "$SLASH_VARIANTS" == "1" ]]; then if [[ "$p" == */ && "$p" != "/" ]]; then printf '%s\n' "${p%/}"; else printf '%s\n' "$p/"; fi; fi; }
accepts=("*/*"); if [[ "$ACCEPT_VARIANTS" == "1" ]]; then accepts+=("application/json" "text/html" "application/x-info-exposure-probe"); fi
echo -e "method\turl\tvariant\taccept\trun\tstatus\tcontent_type\tsize\tlocation\tserver\tallow\tcache_control" > "$OUT"
while IFS= read -r raw; do
  [[ -z "$raw" || "$raw" =~ ^# ]] && continue
  while IFS= read -r p; do
    [[ -z "$p" ]] && continue
    if [[ "$p" =~ ^https?:// ]]; then url="$p"; else url="${BASE%/}/${p#/}"; fi
    for method in HEAD GET OPTIONS; do
      for accept in "${accepts[@]}"; do
        for ((i=1;i<=REPEAT;i++)); do
          tmp=$(mktemp); headers=$(mktemp)
          status=$(curl -k -sS -m 8 -X "$method" -H "Accept: $accept" -D "$headers" -o "$tmp" -w '%{http_code}' "$url" 2>/dev/null || echo "ERR")
          ctype=$(awk 'BEGIN{IGNORECASE=1}/^content-type:/{sub(/\r/,"",$0); print substr($0,index($0,$2)); exit}' "$headers")
          loc=$(awk 'BEGIN{IGNORECASE=1}/^location:/{sub(/\r/,"",$0); print $2; exit}' "$headers")
          srv=$(awk 'BEGIN{IGNORECASE=1}/^server:/{sub(/\r/,"",$0); print substr($0,index($0,$2)); exit}' "$headers")
          allow=$(awk 'BEGIN{IGNORECASE=1}/^allow:/{sub(/\r/,"",$0); print substr($0,index($0,$2)); exit}' "$headers")
          cc=$(awk 'BEGIN{IGNORECASE=1}/^cache-control:/{sub(/\r/,"",$0); print substr($0,index($0,$2)); exit}' "$headers")
          size=$(wc -c < "$tmp" | tr -d ' ')
          safe_url=$(redact_cell "$url"); safe_loc=$(redact_cell "${loc:-}")
          echo -e "$method\t$safe_url\tpath_accept_slash\t$accept\t$i\t$status\t${ctype:-}\t$size\t${safe_loc:-}\t${srv:-}\t${allow:-}\t${cc:-}" >> "$OUT"
          rm -f "$tmp" "$headers"; sleep 0.3
        done
      done
    done
  done < <(make_variants "$raw" | awk '!seen[$0]++')
done < "$PATHS"
echo "Wrote $OUT"
