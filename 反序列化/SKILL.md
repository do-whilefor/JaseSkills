---
name: deserialization-local-verify
description: Use this skill for local authorized deserialization exposure mapping, harmless dynamic validation, evidence-gated status classification, and post-report downgrade review. It must not be used on public, production, third-party, cloud metadata, or non-authorized targets.
---

# deserialization-local-verify

## 适用范围

本 Skill 只适用于已经在本机搭建完成、且用户明确授权的开源项目或本地测试服务。允许处理的对象仅限：本地项目代码、本地测试服务、本地测试数据库、本地消息队列、本地缓存、本地文件目录、本地 CLI、本地测试 fixture、本地 worker、本地 import/export/backup/restore 流程。

调用本 Skill 的目标是建立“项目反序列化暴露地图”，再把候选点转化为无害、本地、可复现、可清理的动态验证。最终结论必须证明或否定：不可信输入是否能进入反序列化入口，是否能触发非预期类型解析、对象构造、魔术方法、钩子函数、回调、setter、readObject/readResolve、__wakeup/__destruct、YAML tag、polymorphic binding、PHAR metadata、session/job/cache/message 解析等行为。

## 不适用范围

不得访问或验证：公网目标、内网敏感地址、云元数据地址、真实生产系统、未授权系统、第三方服务。

不得执行或生成：破坏数据库、删除真实文件、写入真实业务目录、DoS、递归爆炸、巨型 payload、内存耗尽验证、真实攻击链、真实恶意 gadget、真实反弹连接、真实远程命令执行、真实外连、生产环境请求。

中间人攻击类型不属于本 Skill。用户要求加入时，输出“不适用”，并把任务收敛回本地授权反序列化验证。

## 输入要求

| 输入项 | 必填 | 记录字段 | 缺失处理 |
|---|---:|---|---|
| 本地项目路径 | 是 | 绝对路径或相对路径 | 只能审查已提供文件；不得执行动态验证 |
| 授权边界 | 是 | 允许的本地路径、端口、数据库、队列、缓存、目录 | 未给边界时不得请求、写入、启动 worker |
| 运行方式 | 是 | 测试命令、服务启动命令、worker 命令、CLI 命令 | 从项目 README、package、pom、composer、pyproject 等文件推断，并标注“推断” |
| 测试账号/角色/租户 | 动态验证需要 | 账号、角色、租户、token 生成方式 | 相关权限、租户、token 验证保持 candidate |
| 本地服务地址 | HTTP/WebSocket/GraphQL 需要 | localhost、127.0.0.1、::1 或用户明确给出的本机地址 | 非本机地址立即停止请求 |
| 数据库/队列/缓存测试配置 | 对应入口需要 | 测试库、测试队列、测试 cache key 前缀 | 不得写入或投递 |
| 可写测试目录 | 是 | test-output、tmp、fixtures、local-lab 或系统临时目录 | 不得加入 canary 或 marker |
| 允许修改测试文件 | 写 harness 时需要 | test、tests、spec、fixtures、local-lab 下的路径 | 只输出补测计划，不写文件 |

## 输出要求

最终报告必须包含以下部分，字段不得省略。无证据时写“未验证”或“无”。

1. 执行摘要：项目语言、框架、反序列化相关依赖、高风险入口数量、confirmed 数量、candidate 数量、blocked 数量、false positive 数量、最高风险点、尚未覆盖原因。
2. 暴露面总表：ID、入口、数据来源、格式、sink、依赖/函数、权限要求、动态验证状态、结论。
3. 依赖与框架风险映射表：依赖/模块、版本、相关反序列化能力、是否被项目调用、调用路径、输入来源、是否可动态验证、风险等级、证据。
4. 每个问题详情：标题、等级、状态、影响模块、输入入口、反序列化 sink、source 到 sink 调用链、安全控制、绕过点或不足、动态验证命令、正向样本、负向样本、阻断样本、观测证据、marker 证据、日志证据、清理动作、业务影响、修复建议、回归测试建议。
5. 证据清单：证据 ID、类型、文件/命令/请求、说明、可复现性。
6. 修复建议：P0、P1、P2 三档。
7. 降级清单：所有缺少动态证据、marker、负向样本、阻断样本或清理记录的 confirmed 必须降级为 candidate。
8. 补测清单：每个 candidate 的本地动态验证计划。
9. 漏报追查清单：session、remember-me、queue、cache、database blob、import/export、plugin、CLI、legacy parser、parser fallback、compressed/base64 nested payload 等隐藏面扫描结论。
10. 强制自我反查：逐项回答是否漏看、误判、缺证据、缺负向样本、缺清理、缺回归测试。

## 原文复刻规则

以下规则直接来自 TXT 原文，执行时不得弱化。

1. 必须先建立项目反序列化暴露地图，不能直接下结论。
2. source 与 sink 必须分开搜索，再做 source 到 sink 的调用链可达性判断。
3. “依赖是否危险”与“项目是否可达”必须分开；仅因为依赖存在，不允许判定为漏洞。
4. 必须证明依赖被项目真实调用。
5. 必须证明调用参数可能来自不可信输入。
6. 必须验证签名、加密、HMAC、CSRF、权限、租户、白名单、schema、safe loader、长度、来源限制是否阻断。
7. 静态可疑只能标记 candidate。
8. 安全控制确实阻断时标记 blocked。
9. 调用不可达时标记 not reachable。
10. 依赖存在但无项目调用时标记 dependency-only，不得报漏洞。
11. 每个 candidate 必须生成无害动态验证计划。
12. 动态验证必须优先使用本地单元测试、本地集成测试、本地 HTTP 请求、本地 WebSocket 请求、本地 GraphQL 请求、本地队列消息投递、本地 Redis/cache/session 写入读取、本地 import/export 文件解析、本地 CLI 命令、本地 fixture replay、本地 coverage 追踪。
13. canary 只能存在于 test、fixtures、local-lab 或测试输出目录；行为只能是 marker 文件、内存 counter、测试日志、测试数据库临时表或可识别异常。
14. 不得使用真实攻击链、真实恶意 gadget、真实反弹 shell、真实命令执行、真实外连、真实文件破坏、真实数据库破坏、生产请求、DoS 类验证。
15. confirmed 只在同时具备 source、sink、source 到 sink 调用链、本地动态验证、无害 marker、正向样本、负向样本、阻断样本或无阻断说明、日志或断言、清理动作、修复建议、回归测试时使用。
16. 完成第一轮后必须重新审判结果；缺少动态证据的 confirmed 必须降级。
17. 不得只看 controller；必须覆盖 queue、cache、session、import、export、backup、restore、plugin、CLI、worker、dead-letter、failed job、database serialized column、audit replay、event sourcing、legacy parser、parser fallback、content-type confusion、base64/gzip/zip 二次解析。
18. 输出必须遵守“证据优先、动态验证优先、无害验证优先、边界优先”。

## 工程化补强规则

以下规则是为了让 TXT 能被 Claude 稳定执行而新增，不能伪装成 TXT 原文。

1. 为每个发现分配稳定 ID：DS-001、DS-002。为证据分配 EV、CMD、REQ、LOG、MARKER 前缀。
2. 每条 source/sink 证据记录文件路径、函数/方法、行号或搜索命令输出。没有行号时写明原因。
3. 每条动态证据记录工作目录、命令、退出码、输入样本、输出样本、日志位置、marker 位置、清理命令。
4. 本地网络请求只允许 localhost、127.0.0.1、::1 或用户明确给出的本机绑定地址。发现其他地址即停止请求并标记越界。
5. marker 默认写入 `<project>/test-output/deserialization-markers/`。若该目录不存在，只能在授权测试目录内创建。
6. 临时测试代码只允许写入 test、tests、spec、fixtures、local-lab 或用户指定测试目录。不得写入 src/main、app、生产配置或真实业务数据目录。
7. 不能安装新依赖时，使用项目已有测试框架、日志、wrapper instrumentation、coverage trace 或 mock sink。仍无法验证时保留 candidate，并列出缺失条件。
8. Windows 环境优先输出 PowerShell 命令。Linux/macOS 命令只作为等价补充。
9. 没有本地动态证据的结论不得写“已证明”。只能写“静态候选”“可疑路径”“等待补测”。
10. 修复建议必须绑定回归测试位置。没有代码路径时写“未定位测试目录，需先定位后补回归测试”。

## 核心工作流

执行顺序固定。

1. 边界确认：记录本地授权范围、禁止范围、可写测试目录、测试账号、服务端口、数据库/队列/缓存测试配置。
2. 项目结构与语言生态识别：识别语言、框架、关键目录、依赖文件、运行命令。
3. source 全量搜索：覆盖 HTTP、文件上传、JSON/XML/YAML/form/protobuf/msgpack、session、token、cache、queue、WebSocket、GraphQL、webhook、import/export、backup/restore、plugin/theme、CLI、本地 fixture、数据库 serialized blob。
4. sink 全量搜索：按语言生态搜索反序列化、对象绑定、动态类型解析、配置解析、消息解析、模板解析入口。
5. 依赖与框架风险映射：分开记录依赖存在、项目调用、调用参数来源、安全控制、动态验证可能性。
6. source 到 sink 可达性分析：建立文件路径、函数名、调用顺序、参数传播、过滤/签名/schema/白名单位置。
7. candidate 生成：只有满足“source 可能到达 sink”或“sink 参数来源未明但可追踪”时建立 candidate。
8. 无害动态验证设计：为每个 candidate 设计正向样本、负向样本、阻断样本、marker、日志、断言、清理动作。
9. 本地动态验证执行：跑测试、服务、请求、worker、CLI、queue/cache/session 读写、import/export 解析或 fixture replay。
10. 状态判定：按 confirmed、candidate、blocked、not reachable、dependency-only、false positive 分类。
11. 反向审判：检查 confirmed 是否缺动态证据；缺证据即降级。
12. 最终交付：输出报告、证据清单、降级清单、补测清单、漏报追查清单、修复建议、回归测试建议。

## 分阶段执行步骤

### 阶段 1：项目结构与语言生态识别

输出项目语言、框架、关键目录、依赖文件和相关反序列化依赖。

语言和框架至少覆盖：Java/Kotlin/Scala/Spring/Struts/Shiro/Dubbo/Hessian/RMI/JMS/Kafka/RabbitMQ/Redis；PHP/Laravel/Symfony/ThinkPHP/WordPress 插件/Composer；Python/Django/Flask/FastAPI/Celery/pickle/yaml/marshmallow；.NET/ASP.NET/BinaryFormatter/NetDataContractSerializer/LosFormatter/ViewState；Node.js/Express/NestJS/Next.js/serialize-javascript/node-serialize/js-yaml；Ruby/Rails/Marshal/YAML；Go/gob/json/xml custom unmarshal；Rust/serde/custom Deserialize。

关键目录至少覆盖：API 路由、controller/handler/service/middleware、model/entity/DTO、queue/job/task/worker、cache/session/auth、import/export/backup/restore、upload/file parser、plugin/extension/hook、test/fixture/seed。

依赖文件至少覆盖：package.json、pnpm-lock、yarn.lock、pom.xml、build.gradle、composer.json、composer.lock、requirements.txt、pyproject.toml、Pipfile.lock、*.csproj、packages.config、Gemfile.lock、go.mod。

### 阶段 2：source / sink 全量搜索

source 类别至少覆盖：HTTP body/query/path/header/cookie、multipart 文件上传、JSON/XML/YAML/form-data/protobuf/msgpack、session/remember-me/JWT-like token/自定义 token、Redis/Memcached/cache blob、Kafka/RabbitMQ/SQS/JMS/Celery/Sidekiq/queue job payload、WebSocket message、GraphQL variables、webhook payload、import/export 文件、backup/restore 文件、plugin/theme/extension 包、CLI 参数读取的本地文件、生产逻辑引用测试 fixture、数据库 serialized blob 二次解析。

sink 搜索必须按项目语言执行：

| 语言 | sink / 模式 |
|---|---|
| Java/JVM | ObjectInputStream、readObject、readResolve、Externalizable、Serializable、XMLDecoder、XStream、HessianInput、Kryo、Fastjson autoType/parseObject、Jackson enableDefaultTyping/activateDefaultTyping/@JsonTypeInfo、SnakeYAML load、Shiro rememberMe、Dubbo/RMI/JMS message converter |
| PHP | unserialize、__wakeup、__destruct、Serializable、Phar metadata、session_decode、igbinary_unserialize、yaml_parse、custom object hydration |
| Python | pickle.loads/load、dill、cloudpickle、yaml.load without safe loader、marshal.loads、jsonpickle、Celery pickle serializer、__reduce__、__setstate__、object_hook |
| .NET | BinaryFormatter、NetDataContractSerializer、LosFormatter、ObjectStateFormatter、TypeNameHandling、DataContractSerializer unsafe type resolution、ViewState deserialization |
| Node.js | node-serialize、serialize-javascript、js-yaml unsafe schema、custom reviver、vm/Function/eval-adjacent object hydration、cookie/session deserialize wrappers |
| Ruby | Marshal.load、YAML.load、Psych.load、ActiveSupport message verifier deserialization、init_with、encode_with |
| Go | gob.Decoder、custom UnmarshalJSON/UnmarshalXML、mapstructure weak typing、plugin/config loaders、interface{} polymorphic decode |
| Rust | serde Deserialize into enum/interface-like dynamic structures、bincode、rmp-serde、postcard、custom Deserialize impl、plugin/config deserializers |

### 阶段 3：依赖与框架风险映射

必须输出固定表：编号、依赖/模块、版本、相关反序列化能力、是否被项目调用、调用路径、输入来源、是否可动态验证、风险等级、证据。

判定规则：依赖存在但无调用为 dependency-only；有调用但不可由不可信输入触达为 not reachable；source 到 sink 可能可达但未动态验证为 candidate；安全控制阻断为 blocked；满足 confirmed 门槛后才为 confirmed。

### 阶段 4：动态验证设计

每个 candidate 必须包含：验证目标、正向样本、负向样本、阻断样本、观测方式、回滚方式。

正向样本只能使用项目允许格式和无害 marker。负向样本至少覆盖错误类型、非白名单类型、篡改签名、过期 token、无权限用户、其他租户用户、超长输入、非预期 content-type 中适用项。阻断样本记录安全控制位置和错误信息。观测方式使用应用日志、marker 文件、单元测试断言、HTTP 状态码、响应差异、测试数据库临时记录、queue 消费日志、coverage trace 或 debug hook。回滚方式必须清理测试文件、回滚测试数据库、清空测试队列、删除测试 cache key。

### 阶段 5：执行本地动态验证

优先补测试、写 harness、跑服务、发本地请求、跑队列消费者、跑 CLI importer、跑 job worker。允许方式仅限本地单元测试、本地集成测试、本地 HTTP/WebSocket/GraphQL、本地队列消息投递、本地 Redis/cache/session 写入读取、本地 import/export 文件解析、本地 CLI 命令、本地 fixture replay、本地 coverage 追踪。

禁止真实命令执行、真实恶意 gadget、真实外连、真实反弹 shell、真实文件破坏、真实数据库破坏、生产环境请求、DoS、递归爆炸、巨型 payload、内存耗尽验证。

### 阶段 6：构造本地 canary 验证

在语言允许且测试边界允许时，临时加入测试专用 canary 类、canary object、canary handler、canary tag、canary hook 或 mock deserializer。canary 只能位于 test、fixtures、local-lab。唯一行为只能是写 marker、增加内存 counter、写测试日志、写测试数据库临时表、抛出可识别异常。

不能加入 canary 时，改用类型错误差异、schema bypass 差异、日志 marker、mock sink、coverage trace、debugger breakpoint、wrapper instrumentation。

### 阶段 7：偏门和隐藏暴露面专项检查

必须检查：remember-me cookie、session store、password reset token、email verification token、OAuth state/binding token、webhook 重放数据、admin import、backup restore、report template、workflow definition、low-code/form builder、rule engine、plugin/theme/extension installer、avatar/document/archive metadata parser、PHAR-like metadata、YAML/XML/properties 配置导入、cache warming、job retry payload、dead-letter queue、failed job table、audit log replay、event sourcing replay、database serialized column、ORM custom type converter、message converter、RPC codec、mobile API 压缩或加密 body、GraphQL scalar/variables、WebSocket init payload、internal admin-only API、test fixture 被生产代码引用、migration/seed/debug endpoint、CLI maintenance command、SSR/server action 参数绑定、polymorphic JSON/XML type discriminator、hidden frontend 参数被后端接受、content-type confusion、file extension 与 magic header 不一致、base64/gzip/zip 包裹后的 serialized blob、签名验证前先解析对象的逻辑错误。

### 阶段 8：高危判定标准

只有同时满足以下条件，才能标记 confirmed：存在不可信输入 source；输入可达反序列化 sink；sink 使用危险模式或安全配置不足；本地动态验证证明可触发非预期类型解析、对象生命周期方法、hook、callback、custom unmarshal、YAML tag、magic method、setter side effect 或反序列化前置解析；证据包含调用链、触发请求或本地测试命令、输入样本、输出样本、日志、marker、断言、截图或文本证据、清理记录；没有使用破坏性 payload；能说明业务影响。

业务影响只能写认证绕过、权限绕过、任意对象注入、敏感字段篡改、逻辑流转绕过、后台任务伪造、文件读取风险、服务端模板/表达式风险、潜在代码执行风险路径。不得用真实恶意链证明潜在代码执行。

### 阶段 9：输出报告

使用 `templates/output-template.md`。不得改成泛泛报告。字段缺失时写“未验证”，并在补测清单记录缺口。

### 阶段 10：强制自我反查

完成第一轮后必须逐项回答：是否只看 controller；是否把依赖存在误判成漏洞；是否把静态可疑误判成 confirmed；是否缺少动态证据；是否缺少负向样本；是否缺少签名篡改、过期 token、低权限、跨租户测试；是否未验证签名顺序；是否忽略 base64/gzip/zip；是否忽略数据库二阶段反序列化；是否忽略 failed job/dead-letter/retry；是否忽略 import/backup/restore；是否忽略 YAML/XML/JSON polymorphic type；是否忽略 custom unmarshal/magic method/lifecycle hook；是否用了破坏性 payload；是否没有复现命令、marker、清理、回归测试；是否遗漏语言生态典型 sink；是否需要补隐藏面。

任一回答为“是”，必须回到对应阶段补做或降级，不得结束。

### 阶段 11：创新和偏门路线补充

必须复查：双阶段解析、延迟解析、权限错位、租户错位、签名顺序错误、类型白名单缺陷、content-type confusion、文件解析链、老版本兼容、debug/test 代码残留、插件系统、规则引擎、消息系统、缓存系统、前端隐藏参数。

### 阶段 12：最终交付

最终输出必须列出：实际执行过的命令、实际修改或新增的测试文件、实际请求样本、实际日志片段、实际 marker 结果、每个 confirmed 的完整调用链、每个 candidate 缺少的证据、每个 blocked 的阻断控制、每个 false positive 排除原因、修复建议和回归测试代码位置。

## 质量门禁

以下任一门禁失败，最终报告不得标记为通过。

- 未读取项目文件和依赖文件，不得生成最终结论。
- 未建立暴露地图，不得进入漏洞详情。
- 未分离 source、sink、依赖、调用链，不得判定状态。
- 未区分依赖存在和项目可达，不得报告漏洞。
- 未为 candidate 提供正向、负向、阻断样本，不得结束。
- 未执行本地动态验证，不得使用 confirmed。
- 未记录 marker、日志或断言，不得使用 confirmed。
- 未清理测试痕迹，不得使用 confirmed。
- 未覆盖隐藏暴露面，不得声称覆盖完成。
- 未输出降级清单，不得交付。
- 未输出补测清单，不得交付。
- 未输出修复建议和回归测试建议，不得交付。
- 发现公网、生产、破坏性 payload、真实恶意 gadget、真实外连时，必须停止对应动作并改为无害方案。

## 幻觉控制

1. 未读取文件时写“未读取”。
2. 未执行命令时写“未执行”。
3. 未启动服务时写“服务未启动，动态验证未完成”。
4. 未获得测试账号时写“权限/租户验证未覆盖”。
5. 只有搜索命中时不得写漏洞成立。
6. 只有依赖存在时不得写可利用。
7. 只有代码路径时不得写 confirmed。
8. 工程化补强必须标注为新增执行约束，不得写成 TXT 原文。
9. 示例中的结论不得迁移到真实项目。
10. 不得为了补齐报告字段而虚构命令、日志、marker、截图、行号、请求结果。

## 失败处理

| 失败场景 | 处理动作 | 允许结论 |
|---|---|---|
| 本地项目路径缺失 | 停止执行，要求提供路径；若已有片段，仅整理输入缺口 | 未验证 |
| 授权边界缺失 | 不发请求、不写文件、不启动服务 | 未验证 |
| 依赖无法安装 | 使用已有测试框架或静态证据；记录失败命令 | candidate / dependency-only |
| 服务无法启动 | 记录启动命令、错误、日志；转为补测计划 | candidate |
| 无测试账号 | 不做权限、租户、token 结论 | candidate / 未验证 |
| 无可写测试目录 | 不加入 canary；用 mock sink、coverage、日志替代 | candidate / blocked |
| 请求目标不是本机 | 停止请求，记录越界目标 | 不适用 |
| 样本可能破坏数据 | 拒绝执行，改为 marker/canary/可回滚事务 | 未执行 |
| 无法确认签名顺序 | 不写绕过成立，记录补测点 | candidate |
| 动态验证缺 marker 或清理 | confirmed 降级 | candidate |

## 输出格式

最终报告必须使用 `templates/output-template.md` 的字段顺序。每个问题详情必须含 20 个字段。证据、降级、补测、漏报追查、自我反查必须以表格输出。

状态枚举固定为：confirmed、candidate、blocked、not reachable、dependency-only、false positive、未验证。

## 自检清单

- [ ] 是否只处理本地授权范围。
- [ ] 是否先建立暴露地图。
- [ ] 是否分开 source、sink、依赖、调用链。
- [ ] 是否证明依赖被项目调用。
- [ ] 是否证明参数来自不可信输入。
- [ ] 是否验证安全控制位置和效果。
- [ ] 是否每个 candidate 有正向、负向、阻断样本。
- [ ] 是否每个 confirmed 有本地动态验证、marker、日志或断言、清理记录。
- [ ] 是否无动态证据的 confirmed 已降级。
- [ ] 是否覆盖 queue/cache/session/import/export/CLI/plugin/worker/dead-letter/failed job/database blob。
- [ ] 是否没有使用破坏性 payload、真实恶意链、外连、反弹、DoS。
- [ ] 是否输出修复建议和回归测试建议。
- [ ] 是否列明未覆盖原因。

## TXT 到 Skill 映射说明

| TXT 原文位置/标题 | Skill 位置 | 转化方式 | 类型 | 备注 |
|---|---|---|---|---|
| 角色设定 | 适用范围、description | 转成 Skill 调用身份和目标 | 原文复刻 | 保留本地授权、动态验证、证据链 |
| 当前前提 1-8 | 适用范围、不适用范围、输入要求 | 转成边界、禁止项、验证目标 | 原文复刻 | 禁止公网、生产、破坏性验证 |
| 核心任务 | 核心工作流 | 转成 12 步执行链 | 原文复刻 | 不拆分为多个 Skill |
| 第一阶段 | 阶段 1、输出模板第 3 节 | 转成语言、框架、目录、依赖识别 | 原文复刻 | 保留语言生态列表 |
| 第二阶段 source | 阶段 2、输出模板第 4 节 | 转成 source 搜索表 | 原文复刻 | 覆盖 HTTP、queue、cache、DB blob 等 |
| 第二阶段 sink | 阶段 2、输出模板第 5 节 | 转成按语言 sink 表 | 原文复刻 | 保留 Java/PHP/Python/.NET/Node/Ruby/Go/Rust |
| 第三阶段 | 阶段 3、输出模板第 6 节 | 转成依赖风险映射和状态规则 | 原文复刻 | 防止依赖即漏洞 |
| 第四阶段 | 阶段 4、输出模板第 10 节 | 转成补测计划字段 | 原文复刻 | 保留正向、负向、阻断、观测、回滚 |
| 第五阶段 | 阶段 5、质量门禁 | 转成本地动态执行要求 | 原文复刻 | 禁止停留静态审计 |
| 第六阶段 | 阶段 6 | 转成 canary 约束 | 原文复刻 | 限制 test/fixtures/local-lab |
| 第七阶段 | 阶段 7、final-review | 转成隐藏暴露面清单 | 原文复刻 | 防止只看 controller |
| 第八阶段 | 阶段 8、quality-gate | 转成 confirmed 门槛 | 原文复刻 | 缺证据即不能 confirmed |
| 第九阶段 | templates/output-template.md | 转成报告模板 | 原文复刻 | 保留执行摘要、暴露表、详情、证据、修复 |
| 第十阶段 | final-review、输出模板第 15 节 | 转成强制反查 | 原文复刻 | 20 项反查问题 |
| 第十一阶段 | 阶段 11、final-review | 转成偏门路线复查 | 原文复刻 | 双阶段、延迟、错位、fallback 等 |
| 第十二阶段 | 输出要求、输出模板第 9-16 节 | 转成最终交付字段 | 原文复刻 | 命令、文件、请求、日志、marker、清理 |
| 稳定 ID、默认 marker 目录、Windows 命令偏好 | 工程化补强规则 | 新增执行约束 | 工程化补强 | 只为可执行和可验收服务 |
