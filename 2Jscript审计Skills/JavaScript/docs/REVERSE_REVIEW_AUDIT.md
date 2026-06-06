# 原版本反向审查结论

## 原版本主要问题总览

1. 存在工程自测脚本崩溃：`skill_trigger_tester.py` 读取 `data["matches"]`，调度器返回 `chain/all_matches`，测试链不可执行。
2. 压缩包混入 `__pycache__` 和 `.pyc`，影响可复刻性、跨平台可维护性和代码审查洁净度。
3. 自动化脚本能力声明过强，部分脚本是正则/启发式提取，却容易被读者理解为完整 AST/语义解析。
4. `README`、`docs`、`templates`、`schemas`、`scripts` 之间存在引用一致性风险，缺少统一索引自检。
5. 路由器对“帮我整理一下”“只上传文件不说明目标”等上下文型任务支持不足。
6. 原文内容与延伸内容虽有部分标记，但不是全局强制，后续维护容易把延伸误当原文。
7. 测试体系多为 Markdown 描述，缺少可机器执行的 15 类测试样例。
8. 对不可交付原因有规则，但模板和每个 Skill 的输出强制程度不一致。
9. 专项场景拆得过碎，Skill 数量偏多，Electron/Extension/小程序可合并为专项 Skill，降低争抢。
10. 反幻觉规则存在，但没有以 schema + quality gate + package self-check 三层落地。

## 修复策略

- 保留原文三大能力域：静态审计、动态验证、反向审查。
- 将核心 Skills 固定为 00-11，其中 11 合并专项场景。
- 所有 Skill 强制包含触发、禁止触发、输入、步骤、输出、质量门禁、失败处理、反幻觉。
- 添加 `scripts/package_self_check.py`、`scripts/skill_dispatcher.py`、`scripts/skill_trigger_tester.py`、`scripts/strict_quality_gate.py`。
- 添加 JSON 测试样例库，覆盖正常、模糊、负样本、误触发、漏触发、冲突、路径幻觉、工具幻觉、prompt injection、格式、质量门禁、协作、最小路径、专家路径。
