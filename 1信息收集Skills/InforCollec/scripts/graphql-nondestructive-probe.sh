#!/usr/bin/env bash
set -euo pipefail
ENDPOINT=""; OUT="graphql-probe.md"; ALLOW_HOSTS=(localhost 127.0.0.1 0.0.0.0 ::1 '[::1]'); HEADERS=()
usage(){ cat >&2 <<'EOF'
Usage: graphql-nondestructive-probe.sh --endpoint URL [--out FILE] [--allow-host HOST] [--header 'Name: value']
Only performs low-frequency read-only GraphQL probes: OPTIONS, __typename, malformed query, nonexistent field. No mutation, no brute-force schema enumeration, no external token validation.
EOF
exit 2; }
while [[ $# -gt 0 ]]; do case "$1" in --endpoint) ENDPOINT="$2"; shift 2;; --out) OUT="$2"; shift 2;; --allow-host) ALLOW_HOSTS+=("$2"); shift 2;; --header) HEADERS+=("$2"); shift 2;; *) usage;; esac; done
[[ -n "$ENDPOINT" ]] || usage
host=$("${PYTHON:-python3}" - "$ENDPOINT" <<'PY'
import sys, urllib.parse
u=urllib.parse.urlparse(sys.argv[1]); print(u.hostname or '')
PY
)
allowed=0; for h in "${ALLOW_HOSTS[@]}"; do [[ "$host" == "$h" ]] && allowed=1; done
if [[ "$allowed" != "1" ]]; then echo "Refusing non-local/non-allowed host: $host. Use --allow-host $host only for explicitly authorized targets." >&2; exit 3; fi
redact(){ sed -E -e 's/(Authorization:[[:space:]]*Bearer[[:space:]]+)[A-Za-z0-9._-]+/\1****/Ig' -e 's/(token|secret|password|api[_-]?key)(["'"'"' ]*[:=]["'"'"' ]*)[^,"'"'"' ]+/\1\2****/Ig' -e 's/(eyJ[A-Za-z0-9_.-]{20,})/eyJ****/g'; }
curl_args=(-sS -k --max-time 15); for h in "${HEADERS[@]}"; do curl_args+=(-H "$h"); done
probe(){ local name="$1" method="$2" data="${3:-}"; echo "### $name"; echo; echo '- 请求摘要：'; echo '```text'; echo "$method $ENDPOINT" | redact; echo '```'; echo '- 响应摘要：'; echo '```text'; if [[ "$method" == "OPTIONS" ]]; then curl "${curl_args[@]}" -i -X OPTIONS "$ENDPOINT" 2>&1 | head -80 | redact || true; else curl "${curl_args[@]}" -i -X POST -H 'Content-Type: application/json' --data "$data" "$ENDPOINT" 2>&1 | head -120 | redact || true; fi; echo '```'; echo; }
{
echo "# GraphQL 非破坏验证摘要"; echo; echo "- Endpoint: $ENDPOINT"; echo "- Host: $host"; echo "- 生成时间: $(date -Iseconds)"; echo "- 声明: 只读低频验证；不执行 mutation；不爆破字段；默认不执行 introspection。"; echo
probe "OPTIONS / CORS / Allow" OPTIONS
probe "最小只读 query: __typename" POST '{"query":"{ __typename }"}'
probe "不存在字段错误富信息" POST '{"query":"query NonDestructiveProbe { __infoExposureProbeNonexistentField }"}'
probe "格式错误响应" POST '{"query":"query {"}'
echo "## 判定提示"; echo "- 若仅返回 introspection disabled 且无字段、类型、路径、extensions、stack 等额外信息，默认不可报告。"; echo "- 若错误体包含字段建议、内部路径、resolver、serviceName、stack、traceId，应作为候选回流 04 和 07。"
} > "$OUT"
echo "Wrote $OUT"
