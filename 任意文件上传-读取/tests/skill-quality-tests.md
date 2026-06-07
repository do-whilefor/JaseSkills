# Skill Quality Tests

这些测试用于验收本 Skill 是否把 TXT 转成可执行 Skill，而不是摘要、幻觉扩展或空壳。

## 1. TXT 关键内容覆盖测试

- [ ] SKILL.md 是否包含本地授权项目边界。
- [ ] SKILL.md 是否包含禁止公网敏感地址。
- [ ] SKILL.md 是否包含禁止读取真实系统敏感文件。
- [ ] SKILL.md 是否包含只能读取 marker 文件。
- [ ] SKILL.md 是否包含只能写入 marker 测试目录。
- [ ] SKILL.md 是否包含无害 marker 上传限制。
- [ ] SKILL.md 是否包含无动态证据不得 confirmed。
- [ ] SKILL.md 是否包含 confirmed 所需证据字段。
- [ ] SKILL.md 是否包含上传入口验证 14 类要求。
- [ ] SKILL.md 是否包含读取入口验证 14 类要求。
- [ ] SKILL.md 是否包含路径规范化 10 类要求。
- [ ] SKILL.md 是否包含角色/租户权限矩阵。
- [ ] SKILL.md 是否包含语言栈专项。
- [ ] SKILL.md 是否包含反向审判和降级规则。

失败判定：任一核心主题缺失，则不是合格复刻。

## 2. 摘要伪装测试

- [ ] 是否存在只说“检查上传风险”但没有验证对象、证据、通过标准和失败处理的段落。
- [ ] 是否存在只说“检查路径穿越”但没有 marker、请求、响应、before/after 的段落。
- [ ] 是否存在只说“输出报告”但没有报告字段的段落。
- [ ] 是否存在只说“验证权限”但没有角色/租户矩阵的段落。

失败判定：出现上述任一情况，必须改写为步骤、字段、证据和门禁。

## 3. 无关内容测试

- [ ] 是否加入 TXT 未要求的公网扫描能力。
- [ ] 是否加入未授权目标测试能力。
- [ ] 是否加入漏洞利用、持久化、webshell、反弹连接等能力。
- [ ] 是否加入 MITM 分析。
- [ ] 是否加入破坏性资源消耗测试。
- [ ] 是否要求读取真实敏感文件证明漏洞。

失败判定：出现任一无关能力，必须删除。

## 4. 命名测试

- [ ] Skill 名称是否简洁。
- [ ] Skill 名称是否能看出文件边界动态验证主题。
- [ ] 是否避免 best/final/advanced/audit/new/ultimate 等空泛词。
- [ ] 文件名是否短而可辨识。
- [ ] 目录名是否与 TXT 核心主题对应。
- [ ] 是否不存在多个名字表达同一功能。

失败判定：命名空泛、过长或无法对应 TXT 核心主题时必须重命名。

## 5. 目录臃肿测试

- [ ] 是否只有 1 个主 Skill。
- [ ] 是否未拆出空壳 Skill。
- [ ] 是否未创建无内容目录。
- [ ] 每个文件是否有明确作用。
- [ ] 是否未添加不必要脚本。
- [ ] 是否能把映射和 PowerShell 说明放入 README 而非增加孤立文件。

失败判定：无独立调用价值的文件或目录必须删除或合并。

## 6. 输入输出定义测试

- [ ] SKILL.md 是否定义 project_root。
- [ ] SKILL.md 是否定义 local_base_url。
- [ ] SKILL.md 是否定义 auth_contexts。
- [ ] SKILL.md 是否定义 tenant_contexts。
- [ ] SKILL.md 是否定义 test_marker_root。
- [ ] SKILL.md 是否定义 evidence_output_dir。
- [ ] SKILL.md 是否定义 allowed_operations。
- [ ] SKILL.md 是否定义 rollback_policy。
- [ ] output-template.md 是否可直接填写。
- [ ] output-template.md 是否包含验证矩阵。
- [ ] output-template.md 是否包含 evidence manifest。

失败判定：输入或输出字段不完整时必须补齐。

## 7. 质量门禁测试

- [ ] quality-gate.md 是否为可勾选格式。
- [ ] quality-gate.md 是否覆盖授权与边界。
- [ ] quality-gate.md 是否覆盖 Skill 工程门禁。
- [ ] quality-gate.md 是否覆盖 marker 环境。
- [ ] quality-gate.md 是否覆盖项目理解。
- [ ] quality-gate.md 是否覆盖上传验证。
- [ ] quality-gate.md 是否覆盖读取验证。
- [ ] quality-gate.md 是否覆盖路径与二次链路。
- [ ] quality-gate.md 是否覆盖权限和租户。
- [ ] quality-gate.md 是否覆盖依赖专项。
- [ ] quality-gate.md 是否覆盖结论分级。

失败判定：质量门禁无法阻止错误 confirmed 时必须修复。

## 8. 失败处理测试

- [ ] SKILL.md 是否定义项目路径不存在时的处理。
- [ ] SKILL.md 是否定义服务未启动时的处理。
- [ ] SKILL.md 是否定义 marker 创建失败时的处理。
- [ ] SKILL.md 是否定义无角色凭据时的处理。
- [ ] SKILL.md 是否定义无租户环境时的处理。
- [ ] SKILL.md 是否定义日志不可用时的处理。
- [ ] SKILL.md 是否定义请求工具不可用时的处理。
- [ ] SKILL.md 是否定义文件系统状态不可读时的处理。
- [ ] SKILL.md 是否定义回滚失败时的处理。

失败判定：缺失失败处理则不可交付。

## 9. TXT 映射测试

- [ ] SKILL.md 是否包含 TXT 到 Skill 映射说明。
- [ ] README.md 是否列出 TXT 原文位置、关键内容、Skill 位置、复刻类型。
- [ ] 工程化补强是否明确标记。
- [ ] 是否未把新增输入字段、状态枚举、矩阵格式伪装成 TXT 原文。
- [ ] 是否能从每个核心规则追溯到 TXT 章节。

失败判定：无法追溯原文时不可交付。

## 10. 反向审判测试

- [ ] final-review.md 是否能逐条审判 confirmed / candidate / false positive。
- [ ] final-review.md 是否包含遗漏入口反查。
- [ ] final-review.md 是否包含偏门上传复测。
- [ ] final-review.md 是否包含偏门读取复测。
- [ ] final-review.md 是否包含依赖风险反查。
- [ ] final-review.md 是否包含代码结构反查。
- [ ] final-review.md 是否要求重新生成验证矩阵。
- [ ] final-review.md 是否包含严厉降级规则。
- [ ] final-review.md 是否要求输出漏掉、误判、证据不足、未动态验证、未覆盖二次链路、降级漏洞和下一步补测点。

失败判定：不能推翻错误结论的反查清单不可交付。

## 11. 直接可调用测试

让 Claude 只读取 SKILL.md 和一个本地项目路径，观察是否能输出：

- [ ] 输入缺失清单。
- [ ] 授权边界判断。
- [ ] 项目文件处理面清单。
- [ ] marker 环境计划。
- [ ] 上传入口矩阵。
- [ ] 读取入口矩阵。
- [ ] 权限/租户矩阵。
- [ ] 已执行 / 未执行区分。
- [ ] confirmed 降级规则。
- [ ] 最终报告模板字段。

失败判定：如果 Claude 仍只会总结 TXT，则 SKILL.md 规则失败，必须重写为步骤、字段、证据和门禁。
