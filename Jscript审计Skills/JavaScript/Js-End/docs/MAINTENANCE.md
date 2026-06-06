# 维护说明

1. 新增 Skill 必须先更新 `docs/CAPABILITY_INDEX.md` 和 `docs/ROUTING_TABLE.md`。
2. 新增模板必须更新 `templates/` 索引和至少一个测试样例。
3. 新增脚本必须声明“原文能力”或“文档延伸”，并说明输入、输出、失败处理。
4. 任何脚本不得默认联网、不得默认写入目标项目、不得默认执行破坏性动作。
5. 修改后必须运行：

```bash
python3 scripts/package_self_check.py .
python3 scripts/skill_trigger_tester.py
python3 scripts/strict_quality_gate.py tests/sample-manifests/insufficient.json
```

6. 如果质量门禁无法通过，不能发布。
