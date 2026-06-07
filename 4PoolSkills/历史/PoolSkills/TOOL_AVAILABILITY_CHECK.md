# TOOL_AVAILABILITY_CHECK.md

运行：`python .\scripts\toolchain_availability_check.py --root . --out .\outputs\tool_availability.json`

检查 Babel、TypeScript、tree-sitter、Python ast/libcst、JavaParser、PHP-Parser、Ruby Ripper、Go parser、Rust syn、Playwright、Burp、MCP、HAR 路径、jsonschema。缺失工具不得伪装 ready；关联候选最高 `needs_review`。
