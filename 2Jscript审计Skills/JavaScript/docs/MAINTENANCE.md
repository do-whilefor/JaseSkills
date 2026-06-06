# 维护说明

1. 新增 Skill 必须更新 `docs/CAPABILITY_INDEX.md` 和 `docs/ROUTING_TABLE.md`。
2. 新增模板必须更新 `templates/` 并提供至少一个测试样例或 schema 约束。
3. 新增脚本必须说明输入、输出、失败处理和是否能支撑漏洞结论。
4. 任何脚本不得默认联网、不得默认写入目标项目、不得默认执行破坏性动作。
5. 修改后必须运行：

```bash
python scripts/package_self_check.py .
python scripts/skill_trigger_tester.py
python scripts/strict_quality_gate.py tests/sample-manifests/insufficient.json
node scripts/js_cross_platform_runner.mjs windows:validate
```

6. 如果质量门禁无法通过，不得把结论写成 verified。
