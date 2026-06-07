# skill-quality-tests

本文件用于检查该 Skill 是否真正复刻 TXT，而不是摘要、空壳或幻觉扩展。检查可人工勾选，也可转成仓库验收脚本。

## 1. TXT 关键内容覆盖测试

- [ ] SKILL.md 包含本地授权边界。
- [ ] SKILL.md 禁止公网、生产、云元数据、内网敏感地址。
- [ ] SKILL.md 禁止破坏性命令、真实恶意 gadget、外连、反弹、DoS。
- [ ] SKILL.md 要求先建立反序列化暴露地图。
- [ ] SKILL.md 包含项目语言和框架识别。
- [ ] SKILL.md 包含关键目录识别。
- [ ] SKILL.md 包含依赖清单识别。
- [ ] SKILL.md 包含 source 全量搜索类别。
- [ ] SKILL.md 包含按语言 sink 搜索清单。
- [ ] SKILL.md 区分依赖存在、项目调用、输入来源。
- [ ] SKILL.md 包含 candidate 动态验证计划。
- [ ] SKILL.md 包含本地动态验证要求。
- [ ] SKILL.md 包含 canary 约束。
- [ ] SKILL.md 包含隐藏暴露面专项检查。
- [ ] SKILL.md 包含 confirmed 判定门槛。
- [ ] SKILL.md 包含最终输出格式。
- [ ] SKILL.md 包含强制自我反查。
- [ ] SKILL.md 包含偏门路线补充。
- [ ] SKILL.md 包含最终交付证据要求。

失败处理：任一项缺失，直接修复对应文件，不得只写“待补”。

## 2. 摘要替代复刻测试

以下问题全部应为“否”。

- [ ] 是否只写“检查反序列化风险”，没有 source/sink/动态验证/证据字段。
- [ ] 是否没有列出具体 source 类型。
- [ ] 是否没有列出具体 sink 类型。
- [ ] 是否没有状态判定规则。
- [ ] 是否没有 confirmed 降级规则。
- [ ] 是否没有正向/负向/阻断样本要求。
- [ ] 是否没有 marker、日志、断言、清理要求。

## 3. 无关内容测试

以下问题全部应为“否”。

- [ ] 是否加入中间人攻击流程。
- [ ] 是否加入公网扫描流程。
- [ ] 是否加入生产环境验证流程。
- [ ] 是否加入真实 exploit/gadget/命令执行样本。
- [ ] 是否加入与反序列化无关的漏洞扩展目录。
- [ ] 是否加入没有被 TXT 要求且不能服务本地无害验证的文件。

## 4. 命名测试

- [ ] Skill 文件夹名简洁。
- [ ] Skill 文件夹名能看出来自反序列化主题。
- [ ] 未使用 best、final、new、advanced、ultimate、skill-only。
- [ ] 文件名短且能看出作用。
- [ ] 无中文乱码风险路径。

当前名称：`deserialization-local-verify`。

## 5. 目录臃肿测试

- [ ] 只保留 1 个主 Skill。
- [ ] 未拆出无法独立执行的子 Skill。
- [ ] 无空目录。
- [ ] 无空文件。
- [ ] 未增加 rules/workflows/schemas/fixtures 目录。
- [ ] 每个文件都有明确验收作用。

## 6. 输入输出定义测试

- [ ] SKILL.md 明确输入要求。
- [ ] SKILL.md 明确缺失输入的失败处理。
- [ ] templates/output-template.md 有可填写字段。
- [ ] templates/output-template.md 包含执行摘要、暴露面总表、问题详情、证据清单、修复建议。
- [ ] templates/output-template.md 包含降级清单、补测清单、漏报追查清单。

## 7. 质量门禁测试

- [ ] checklists/quality-gate.md 为可勾选格式。
- [ ] 包含授权边界门禁。
- [ ] 包含非破坏验证门禁。
- [ ] 包含暴露地图门禁。
- [ ] 包含依赖可达门禁。
- [ ] 包含动态证据门禁。
- [ ] 包含隐藏面门禁。
- [ ] 包含状态门禁。
- [ ] 包含修复回归门禁。

## 8. 失败处理测试

- [ ] SKILL.md 说明项目无法安装依赖时不得 confirmed。
- [ ] SKILL.md 说明服务无法启动时如何处理。
- [ ] SKILL.md 说明无测试账号时如何处理。
- [ ] SKILL.md 说明无法加入 canary 时如何处理。
- [ ] SKILL.md 说明请求目标不是本机时如何处理。
- [ ] SKILL.md 说明样本可能破坏数据时如何处理。
- [ ] SKILL.md 说明无法确认签名顺序时如何处理。

## 9. TXT 映射测试

- [ ] SKILL.md 包含 TXT 到 Skill 映射说明。
- [ ] 映射表覆盖 TXT 角色设定、当前前提、核心任务、第 1 到第 12 阶段、重新审判段落。
- [ ] 映射表区分原文复刻和工程化补强。
- [ ] 工程化补强没有伪装成 TXT 原文。

## 10. 工程化补强边界测试

- [ ] 证据 ID 规则标注为工程化补强。
- [ ] 默认 marker 目录标注为工程化补强。
- [ ] Windows PowerShell 偏好标注为落地辅助。
- [ ] 未把新增执行约束说成 TXT 明确要求。

## 11. 示例测试

- [ ] basic-example.md 展示 candidate 不能 confirmed。
- [ ] basic-example.md 展示 blocked。
- [ ] basic-example.md 展示 dependency-only。
- [ ] full-example.md 展示降级清单。
- [ ] full-example.md 展示补测清单。
- [ ] full-example.md 展示漏报追查清单。
- [ ] 示例不包含真实恶意 payload。

## 12. 空壳测试

- [ ] 每个 markdown 文件大于 200 字节。
- [ ] 模板不只有标题。
- [ ] checklist 不只有口号。
- [ ] examples 有输入、表格、状态判定和证据字段。
- [ ] tests 能发现漏复刻、幻觉扩展、空壳文件、命名失败、缺质量门禁。

## 13. 最终验收结论

只有全部通过，才允许交付该 Skill。任一测试失败，必须修改文件并重新检查。
