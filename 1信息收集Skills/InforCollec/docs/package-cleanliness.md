# 包清洁规则

发布包只保留正常使用、验证和维护所需文件。更新说明、修复报告、生成哈希清单、缓存、自测输出和旧文件树不进入发布包。

必须保留：

- `SKILL.md` 与各 Skill 目录。
- `scripts/`、`schemas/`、`detectors/`、`dashboard/`、`runtime/`。
- `templates/` 中的漏洞模板、报告模板和质量门模板。
- `knowledge/` 中的知识库内容和占位文件。
- `tests/` 与 `examples/`，用于自测和回归。

不得把候选结果、模板、矩阵或文档声明宣传为确认漏洞。
