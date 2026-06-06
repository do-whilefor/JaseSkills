# Parser plugin registry v3

This directory records what the extractor can actually prove locally.

Status model:

- `builtin_full_ast`: bundled parser backed by the runtime standard library. Currently Python `ast`.
- `builtin_ast_lite`: bundled structured parser with route/symbol/import/sink provenance. It is useful for graph construction but is not claimed as full language AST equivalence.
- `optional_full_ast`: external backend that must pass runtime probe before any report may call it ready.
- `optional_generic_ast`: tree-sitter or similar backend, also runtime-probed.

Required reporting rule: if a parser is `missing`, `manual_required`, or `ast_lite`, findings may be mapped candidates only. Confirmed findings require code evidence, dynamic evidence, negative control, and quality gate pass.
