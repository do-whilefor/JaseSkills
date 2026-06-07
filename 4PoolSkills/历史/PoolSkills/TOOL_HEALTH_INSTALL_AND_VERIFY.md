# 本机工具健康度安装与验证

任何工具未安装、未配置、无法执行，都必须显示为 `missing`、`failed`、`manual_required` 或 `degraded`。禁止在未检测的情况下写 ready。

建议运行：
```powershell
python scripts/tool_health_score.py
python scripts/toolchain_strict_verify.py
```

关键依赖：Node.js、Babel、TypeScript、Python Playwright、tree_sitter、libcst、JavaParser jar、Composer + nikic/php-parser、Ruby Ripper、Go、Rust cargo/syn、Burp、MCP。
