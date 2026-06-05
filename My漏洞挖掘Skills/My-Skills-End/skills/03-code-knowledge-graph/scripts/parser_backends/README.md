# Parser backends v4.3

Java/PHP/Go/Rust/Ruby full AST promotion is blocked until runtime probes pass.

Required checks:

- Java: `JAVAPARSER_CLI` must point to a local JavaParser CLI jar and `java -jar $JAVAPARSER_CLI --probe` must pass.
- PHP: `php` and composer-installed `nikic/php-parser` autoload must be available.
- Go: `go run skills/03-code-knowledge-graph/scripts/parser_backends/go_parser_bridge.go --probe` must pass.
- Rust: cargo must build `skills/03-code-knowledge-graph/scripts/parser_backends/rust_syn_bridge` and `--probe` must pass.
- Ruby: `ruby -rripper` probe must pass.

AST-lite results may create candidates. They cannot satisfy promoted/full-AST claims.
