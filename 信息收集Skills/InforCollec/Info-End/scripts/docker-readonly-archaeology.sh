#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${PWD}"; OUT="docker-readonly-archaeology.md"; ALLOW_HISTORY=1
usage(){ cat >&2 <<'EOF'
Usage: docker-readonly-archaeology.sh [--project-dir DIR] [--out FILE] [--no-history]
Read-only Docker archaeology summary for authorized local projects. Metadata only; no volume content reads; no container modifications.
EOF
exit 2; }
while [[ $# -gt 0 ]]; do case "$1" in --project-dir) PROJECT_DIR="$2"; shift 2;; --out) OUT="$2"; shift 2;; --no-history) ALLOW_HISTORY=0; shift;; *) usage;; esac; done
redact(){ sed -E -e 's/(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret)([=: ][^,; ]+)/\1=****/Ig' -e 's#(mysql|postgres|postgresql|mongodb|redis)://([^:@/]+):([^@/]+)@#\1://\2:****@#Ig' -e 's/(eyJ[A-Za-z0-9_.-]{20,})/eyJ****/g'; }
{
echo "# Docker 只读考古摘要"; echo; echo "- 项目目录：$PROJECT_DIR"; echo "- 生成时间：$(date -Iseconds)"; echo "- 只读声明：不读取 volume 文件内容，不修改容器，不执行容器内命令，不导出镜像层文件。"; echo
if ! command -v docker >/dev/null 2>&1; then echo "## Docker 状态"; echo "docker 命令不可用，容器层考古未覆盖。"; exit 0; fi
echo "## docker ps"; echo '```text'; docker ps --format 'table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Ports}}\t{{.Status}}' 2>&1 | redact || true; echo '```'; echo
echo "## Compose 文件候选"; echo '| 文件 | 摘要 |'; echo '|---|---|'; find "$PROJECT_DIR" -maxdepth 3 \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose*.yml' -o -name 'compose*.yaml' \) 2>/dev/null | while read -r f; do summary=$(grep -E '^[[:space:]]*(image:|build:|ports:|volumes:|env_file:|environment:|networks:)' "$f" 2>/dev/null | head -20 | tr '\n' '; ' | redact); printf '| `%s` | `%s` |\n' "$f" "$summary"; done; echo
ids=$(docker ps -q 2>/dev/null || true); if [[ -z "$ids" ]]; then echo "## 容器 inspect 摘要"; echo "未发现运行中的容器。"; else echo "## 容器 inspect 摘要"; for id in $ids; do echo; echo "### 容器 $id"; name=$(docker inspect -f '{{.Name}}' "$id" 2>/dev/null | sed 's#^/##' | redact || true); image=$(docker inspect -f '{{.Config.Image}}' "$id" 2>/dev/null | redact || true); echo "- Name: $name"; echo "- Image: $image"; echo "- Entrypoint/Cmd: $(docker inspect -f '{{json .Config.Entrypoint}} {{json .Config.Cmd}}' "$id" 2>/dev/null | redact || true)"; echo "- WorkingDir: $(docker inspect -f '{{.Config.WorkingDir}}' "$id" 2>/dev/null | redact || true)"; echo; echo "#### Env keys"; echo '```text'; docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$id" 2>/dev/null | sed -E 's/^([^=]+)=.*$/\1=****/' | sort | redact || true; echo '```'; echo; echo "#### Mounts / Volumes"; echo '| Type | Source/Name | Destination | RW |'; echo '|---|---|---|---|'; docker inspect -f '{{range .Mounts}}{{printf "%s\t%s\t%s\t%v\n" .Type .Source .Destination .RW}}{{end}}' "$id" 2>/dev/null | while IFS=$'\t' read -r t s d rw; do [[ -z "${t:-}" ]] && continue; printf '| `%s` | `%s` | `%s` | `%s` |\n' "$t" "$s" "$d" "$rw" | redact; done; echo; echo "#### Ports / Networks"; echo '```text'; docker inspect -f 'Ports={{json .NetworkSettings.Ports}} Networks={{json .NetworkSettings.Networks}}' "$id" 2>/dev/null | redact || true; echo '```'; echo; if [[ "$ALLOW_HISTORY" == "1" ]]; then imgid=$(docker inspect -f '{{.Image}}' "$id" 2>/dev/null || true); echo "#### Image history"; echo '```text'; docker image history --no-trunc "$imgid" 2>/dev/null | head -30 | redact || true; echo '```'; fi; done; fi
echo; echo "## Volume 列表摘要"; echo '```text'; docker volume ls 2>/dev/null | redact || true; echo '```'; echo; echo "## 不可报告/待确认提示"; echo "- 本脚本仅输出 Docker 元数据摘要，不读取 volume 内容。"; echo "- 发现 env key、mount、image history 中的敏感线索只能作为候选，必须回流 04 做运行态验证，回流 07 做脱敏和质量门禁。"
} > "$OUT"
echo "Wrote $OUT"
