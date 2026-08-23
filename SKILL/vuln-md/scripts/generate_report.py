#!/usr/bin/env python3
"""Generate deterministic Chinese Markdown vulnerability reports."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_SEVERITIES = {"严重", "高危", "中危", "低危"}
REQUIRED_FIELDS = (
    "title",
    "domain",
    "vulnerability_type",
    "severity",
    "summary",
    "location",
    "affected_parameters",
    "steps",
    "recommendations",
)
REQUIRED_STEP_FIELDS = ("title", "method", "description", "inputs", "outputs", "result")
REQUIRED_BLOCK_FIELDS = ("label", "kind", "content")
REQUEST_LINE_RE = re.compile(
    r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|CONNECT|TRACE|PROPFIND|PROPPATCH|MKCOL|COPY|MOVE|LOCK|UNLOCK)\s+\S+\s+HTTP/1\.[01]$",
    re.IGNORECASE,
)
RESPONSE_LINE_RE = re.compile(r"^HTTP/1\.[01]\s+\d{3}(?:\s+.*)?$", re.IGNORECASE)
HEADER_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+:\s?.*$")
SUMMARY_FORBIDDEN_RE = re.compile(
    r"https?://|\bwww\.|\bcurl\b|\bpayload\b|```|\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/",
    re.IGNORECASE,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fixed-structure Markdown vulnerability report from UTF-8 JSON."
    )
    parser.add_argument("--input", required=True, help="UTF-8 JSON input file")
    parser.add_argument("--output", help="Output .md path; required unless --check-only")
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Allow incomplete input and visibly mark placeholders",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate input without writing Markdown",
    )
    return parser


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple)):
        return not value
    return False


def as_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def single_line(value: Any, fallback: str = "待补充") -> str:
    text = normalize_newlines(str(value or "")).strip()
    text = re.sub(r"\s+", " ", text)
    return text or fallback


def escape_inline(value: Any) -> str:
    text = single_line(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("`", "\\`")


def language_tag(value: Any) -> str:
    tag = re.sub(r"[^A-Za-z0-9_+#.-]", "", str(value or "text"))
    return tag or "text"


def split_packet(packet: str) -> tuple[list[str], str] | None:
    normalized = normalize_newlines(packet)
    if "\n\n" not in normalized:
        return None
    head, body = normalized.split("\n\n", 1)
    return head.split("\n"), body


def validate_http_packet(packet: Any, kind: str, label: str) -> list[str]:
    if not isinstance(packet, str) or not packet.strip():
        return [f"{label} 缺少可重放 HTTP 内容"]
    errors: list[str] = []
    if "```" in packet:
        errors.append(f"{label} 含 Markdown 围栏")
    parts = split_packet(packet)
    if parts is None:
        errors.append(f"{label} 的 HTTP 头和正文之间缺少空行")
        return errors
    head_lines, _body = parts
    start_line = head_lines[0].strip() if head_lines else ""
    if kind == "http-request":
        if not REQUEST_LINE_RE.fullmatch(start_line):
            errors.append(f"{label} 请求行不是可重放的 HTTP/1.x 格式")
    elif not RESPONSE_LINE_RE.fullmatch(start_line):
        errors.append(f"{label} 状态行不是完整 HTTP/1.x 格式")
    headers = head_lines[1:]
    for line_number, header in enumerate(headers, start=2):
        if not header or not HEADER_RE.fullmatch(header):
            errors.append(f"{label} 第 {line_number} 行不是合法 HTTP 头")
    if kind == "http-request" and not any(h.lower().startswith("host:") for h in headers):
        errors.append(f"{label} 缺少 Host 头")
    return errors


def validate_blocks(blocks: Any, path: str, direction: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(blocks, list) or not blocks:
        return [f"{path} 必须是非空数组"]
    for index, block in enumerate(blocks, start=1):
        block_path = f"{path}[{index}]"
        if not isinstance(block, dict):
            errors.append(f"{block_path} 必须是对象")
            continue
        for field in REQUIRED_BLOCK_FIELDS:
            if is_blank(block.get(field)):
                errors.append(f"{block_path}.{field} 缺失")
        kind = str(block.get("kind", "")).strip()
        replayable = block.get("replayable", False)
        if not isinstance(replayable, bool):
            errors.append(f"{block_path}.replayable 必须是布尔值")
        if replayable:
            expected_kind = "http-request" if direction == "input" else "http-response"
            if kind != expected_kind:
                errors.append(f"{block_path} 声明可重放时 kind 必须为 {expected_kind}")
            else:
                errors.extend(validate_http_packet(block.get("content"), kind, block_path))
    return errors


def validate_report(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in data or is_blank(data.get(field)):
            errors.append(f"缺少必填字段: {field}")

    severity = str(data.get("severity", "")).strip()
    if severity and severity not in ALLOWED_SEVERITIES:
        errors.append("severity 只能是：严重、高危、中危、低危")

    summary = str(data.get("summary", ""))
    if summary and SUMMARY_FORBIDDEN_RE.search(summary):
        errors.append("summary 不得包含 URL、Payload、curl、代码围栏或原始请求行")

    for field in ("affected_parameters", "recommendations"):
        value = data.get(field)
        if value is not None and (not isinstance(value, list) or not as_text_list(value)):
            errors.append(f"{field} 必须是非空字符串数组")

    steps = data.get("steps")
    if steps is not None and (not isinstance(steps, list) or not steps):
        errors.append("steps 必须是非空数组")
        return errors
    for step_index, step in enumerate(steps or [], start=1):
        path = f"steps[{step_index}]"
        if not isinstance(step, dict):
            errors.append(f"{path} 必须是对象")
            continue
        for field in REQUIRED_STEP_FIELDS:
            if is_blank(step.get(field)):
                errors.append(f"{path}.{field} 缺失")
        preconditions = step.get("preconditions", [])
        if not isinstance(preconditions, list):
            errors.append(f"{path}.preconditions 必须是字符串数组")
        errors.extend(validate_blocks(step.get("inputs"), f"{path}.inputs", "input"))
        errors.extend(validate_blocks(step.get("outputs"), f"{path}.outputs", "output"))
    return errors


def fenced_block(content: Any, language: Any) -> list[str]:
    text = normalize_newlines(str(content or "待补充")).strip("\n") or "待补充"
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"{fence}{language_tag(language)}", text, fence]


def render_artifacts(blocks: Any, heading: str) -> list[str]:
    valid_blocks = blocks if isinstance(blocks, list) and blocks else [
        {"label": "待补充", "kind": "other", "language": "text", "content": "待补充"}
    ]
    lines: list[str] = []
    for index, block in enumerate(valid_blocks, start=1):
        item = block if isinstance(block, dict) else {}
        lines.extend(
            [
                f"#### {heading} {index}：{single_line(item.get('label'))}",
                "",
                f"- 类型：`{language_tag(item.get('kind', 'other'))}`",
                f"- 可直接重放：{'是' if item.get('replayable') is True else '否'}",
                "",
                *fenced_block(item.get("content"), item.get("language")),
                "",
            ]
        )
    return lines


def render_report(data: dict[str, Any], draft: bool, errors: list[str]) -> str:
    title = single_line(data.get("title"))
    domains = as_text_list(data.get("domain")) or ["待补充"]
    locations = as_text_list(data.get("location")) or ["待补充"]
    parameters = as_text_list(data.get("affected_parameters")) or ["待补充"]
    recommendations = as_text_list(data.get("recommendations")) or ["待补充"]
    steps = data.get("steps") if isinstance(data.get("steps"), list) else []

    lines = [
        f"# {title}",
        "",
    ]
    if draft:
        lines.extend(
            [
                "> [!WARNING]",
                "> 本报告为草稿，存在缺失字段或未通过校验的证据，不可作为正式报告提交。",
                *[f"> - {single_line(error)}" for error in errors[:10]],
                "",
            ]
        )

    lines.extend(
        [
            "## 基本信息",
            "",
            "| 字段 | 内容 |",
            "| --- | --- |",
            f"| 漏洞标题 | {escape_inline(title)} |",
            f"| 漏洞域名 | {'<br>'.join(escape_inline(item) for item in domains)} |",
            f"| 漏洞类型 | {escape_inline(data.get('vulnerability_type'))} |",
            f"| 漏洞等级 | **{escape_inline(data.get('severity'))}** |",
            f"| 漏洞 URL / 功能点 | {'<br>'.join(escape_inline(item) for item in locations)} |",
            "",
            "## 1. 漏洞简述",
            "",
            single_line(data.get("summary")),
            "",
            "## 2. 漏洞 URL / 功能点",
            "",
            *[f"- `{single_line(item)}`" for item in locations],
            "",
            "## 3. 影响参数",
            "",
            *[f"- {single_line(item)}" for item in parameters],
            "",
            "## 4. 复现步骤",
            "",
        ]
    )

    if not steps:
        steps = [{}]
    for step_index, step in enumerate(steps, start=1):
        item = step if isinstance(step, dict) else {}
        preconditions = as_text_list(item.get("preconditions")) or ["无"]
        lines.extend(
            [
                f"### 步骤 {step_index}：{single_line(item.get('title'))}",
                "",
                f"**复现方式：** {single_line(item.get('method'))}",
                "",
                "**前置条件：**",
                "",
                *[f"- {single_line(value)}" for value in preconditions],
                "",
                "**步骤说明：**",
                "",
                single_line(item.get("description")),
                "",
                *render_artifacts(item.get("inputs"), "输入 / 操作"),
                *render_artifacts(item.get("outputs"), "响应 / 结果"),
                f"**验证结果：** {single_line(item.get('result'))}",
                "",
            ]
        )

    lines.extend(
        [
            "## 5. 修复建议",
            "",
            *[f"{index}. {single_line(item)}" for index, item in enumerate(recommendations, start=1)],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.is_file():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 2
    try:
        data = json.loads(input_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read JSON input: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("ERROR: top-level JSON value must be an object", file=sys.stderr)
        return 2

    errors = validate_report(data)
    if errors:
        stream = sys.stdout if args.draft else sys.stderr
        print("Validation issues:", file=stream)
        for error in errors:
            print(f"- {error}", file=stream)
        if not args.draft:
            return 2
    else:
        print("Validation OK")

    if args.check_only:
        return 0
    if not args.output:
        print("ERROR: --output is required unless --check-only is used", file=sys.stderr)
        return 2
    output_path = Path(args.output).expanduser().resolve()
    if output_path.suffix.lower() != ".md":
        print("ERROR: output path must end with .md", file=sys.stderr)
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown = render_report(data, args.draft, errors)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
    print(f"Created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
