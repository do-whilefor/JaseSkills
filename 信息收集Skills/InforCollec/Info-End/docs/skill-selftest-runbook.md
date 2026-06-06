# Skill 自测规范

用途：防止后续维护时删除 SKILL.md 的必备结构。该能力是“基于文档延伸”。

## 检查项

每个 SKILL.md 必须包含：

1. 一句话用途。
2. 必须调用条件。
3. 禁止调用条件。
4. 输入。
5. 执行步骤。
6. 输出。
7. 检查点或质量门槛。
8. 失败处理。
9. 跨 Skill 协作或交接。
10. Prompt Injection 抗性。
11. 证据可追溯规则。
12. 延伸内容标记。

## 命令

```bash
python3 scripts/skill-selftest.py . --out skill-selftest-report.json
```

如果结果为 FAIL，必须修复缺失项，不得仅修改脚本阈值来通过测试。
