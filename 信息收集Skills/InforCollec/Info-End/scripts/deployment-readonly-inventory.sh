#!/usr/bin/env bash
set -euo pipefail
ROOT="${PWD}"; OUT="deployment-readonly-inventory.md"; MAX_DEPTH=5
usage(){ echo "Usage: $0 [--root DIR] [--out FILE] [--max-depth N]" >&2; exit 2; }
while [[ $# -gt 0 ]]; do case "$1" in --root) ROOT="$2"; shift 2;; --out) OUT="$2"; shift 2;; --max-depth) MAX_DEPTH="$2"; shift 2;; *) usage;; esac; done
redact(){ sed -E -e 's/(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret)([=: ][^,; ]+)/\1=****/Ig' -e 's#(mysql|postgres|postgresql|mongodb|redis)://([^:@/]+):([^@/]+)@#\1://\2:****@#Ig' -e 's/(eyJ[A-Za-z0-9_.-]{20,})/eyJ****/g'; }
match_files(){ find "$ROOT" -maxdepth "$MAX_DEPTH" -type f \( -name 'Dockerfile*' -o -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose*.yml' -o -name 'compose*.yaml' -o -name '*.service' -o -name 'supervisord*.conf' -o -name 'nginx*.conf' -o -name 'httpd*.conf' -o -name 'apache*.conf' -o -name 'Caddyfile' -o -name 'traefik*.yml' -o -name 'traefik*.yaml' -o -name '.gitlab-ci.yml' -o -name 'Jenkinsfile' -o -name 'azure-pipelines*.yml' -o -name 'circle.yml' -o -path '*/.github/workflows/*' -o -path '*/k8s/*.yml' -o -path '*/k8s/*.yaml' -o -path '*/kubernetes/*.yml' -o -path '*/kubernetes/*.yaml' -o -path '*/helm/*' \) 2>/dev/null | sort; }
{
echo "# 部署信息只读 Inventory"; echo
echo "- 项目目录：$ROOT"; echo "- 生成时间：$(date -Iseconds)"; echo "- 声明：只读扫描项目文件；不连接外部服务；不修改文件；不把静态线索当结论。"; echo
echo "## 部署文件候选"; echo '| 编号 | 类型 | 文件 | 线索摘要 | 下一步 |'; echo '|---|---|---|---|---|'
i=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue; i=$((i+1)); type="other"
  case "$f" in *compose*.yml|*compose*.yaml|*Dockerfile*) type="docker/compose";; *.service|*supervisord*.conf) type="systemd/supervisor";; *nginx*.conf|*httpd*.conf|*apache*.conf|*Caddyfile|*traefik*) type="reverse-proxy";; *.gitlab-ci.yml|*Jenkinsfile*|*azure-pipelines*|*circle.yml|*/.github/workflows/*) type="ci-cd";; */k8s/*|*/kubernetes/*|*/helm/*) type="kubernetes/helm";; esac
  summary=$(grep -E '^[[:space:]]*(image:|build:|ports:|targetPort:|nodePort:|host:|hosts:|server_name|proxy_pass|root|alias|env_file:|environment:|EnvironmentFile=|Environment=|ExecStart=|WorkingDirectory=|artifact|artifacts:|upload|cache:|secret|configMap|volumeMounts:|volumes:|service:|ingress:)' "$f" 2>/dev/null | head -30 | tr '\n' '; ' | redact)
  printf '| DPLY-%03d | `%s` | `%s` | `%s` | 回流 02/03/04/07 |\n' "$i" "$type" "${f#$ROOT/}" "$summary"
done < <(match_files)
if [[ "$i" -eq 0 ]]; then echo '| - | - | - | 未发现常见部署文件 | - |'; fi
echo; echo "## 不可报告提示"; echo "- 该脚本只产生部署静态候选。"; echo "- ports、host、proxy、env key、artifact、volume 线索必须回流运行态验证与质量门禁。"
} > "$OUT"
echo "Wrote $OUT"
