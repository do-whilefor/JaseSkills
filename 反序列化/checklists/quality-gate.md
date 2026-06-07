# quality-gate

本清单用于执行中门禁。任一必需项未通过，不得把结果标记为最终通过。

## A. 授权边界门禁

- [ ] 已记录本地项目路径。
- [ ] 已记录授权边界。
- [ ] 已记录允许访问的本地端口。
- [ ] 已记录允许使用的测试数据库、队列、缓存。
- [ ] 已记录允许写入的测试目录。
- [ ] 未访问公网目标。
- [ ] 未访问内网敏感地址。
- [ ] 未访问云元数据地址。
- [ ] 未请求生产系统。
- [ ] 未使用第三方非授权服务。

失败处理：停止对应动作，将受影响结论标记为未验证。

## B. 非破坏验证门禁

- [ ] 所有样本均为无害 marker、canary、测试目录、测试日志、测试数据库临时表、可回滚事务或 mock sink。
- [ ] 未使用真实攻击链。
- [ ] 未使用真实恶意 gadget。
- [ ] 未执行真实命令。
- [ ] 未进行真实外连。
- [ ] 未进行真实反弹连接。
- [ ] 未破坏文件。
- [ ] 未破坏数据库。
- [ ] 未进行 DoS、递归爆炸、巨型 payload 或内存耗尽验证。

失败处理：拒绝执行危险样本，改写为 canary 或 marker 验证。

## C. 暴露地图门禁

- [ ] 已识别语言和框架。
- [ ] 已识别 API 路由目录。
- [ ] 已识别 controller/handler/service/middleware。
- [ ] 已识别 model/entity/DTO。
- [ ] 已识别 queue/job/task/worker。
- [ ] 已识别 cache/session/auth。
- [ ] 已识别 import/export/backup/restore。
- [ ] 已识别 upload/file parser。
- [ ] 已识别 plugin/extension/hook。
- [ ] 已识别 test/fixture/seed。
- [ ] 已识别依赖文件。

失败处理：补齐目录与依赖识别；无法访问的路径写“未验证”。

## D. source 搜索门禁

- [ ] HTTP body/query/path/header/cookie 已检查。
- [ ] multipart 文件上传已检查。
- [ ] JSON/XML/YAML/form-data/protobuf/msgpack 已检查。
- [ ] session/remember-me/JWT-like token/自定义 token 已检查。
- [ ] Redis/Memcached/cache blob 已检查。
- [ ] queue/job payload 已检查。
- [ ] WebSocket message 已检查。
- [ ] GraphQL variables 已检查。
- [ ] webhook payload 已检查。
- [ ] import/export 文件已检查。
- [ ] backup/restore 文件已检查。
- [ ] plugin/theme/extension 包已检查。
- [ ] CLI 参数读取本地文件已检查。
- [ ] 测试 fixture 被生产逻辑引用已检查。
- [ ] 数据库 serialized blob 二次解析已检查。

失败处理：漏项补搜；无法验证项进入尚未覆盖原因。

## E. sink 搜索门禁

- [ ] 已按项目语言搜索对应 sink。
- [ ] Java/JVM 项目已检查 ObjectInputStream、readObject、readResolve、XMLDecoder、XStream、HessianInput、Kryo、Fastjson、Jackson default typing、SnakeYAML、Shiro rememberMe、Dubbo/RMI/JMS converter。
- [ ] PHP 项目已检查 unserialize、__wakeup、__destruct、Serializable、Phar metadata、session_decode、igbinary_unserialize、yaml_parse、custom object hydration。
- [ ] Python 项目已检查 pickle、dill、cloudpickle、yaml.load、marshal、jsonpickle、Celery pickle serializer、__reduce__、__setstate__、object_hook。
- [ ] .NET 项目已检查 BinaryFormatter、NetDataContractSerializer、LosFormatter、ObjectStateFormatter、TypeNameHandling、ViewState。
- [ ] Node.js 项目已检查 node-serialize、serialize-javascript、js-yaml unsafe schema、custom reviver、vm/Function/eval-adjacent hydration、cookie/session wrappers。
- [ ] Ruby 项目已检查 Marshal.load、YAML.load、Psych.load、ActiveSupport message verifier、init_with、encode_with。
- [ ] Go 项目已检查 gob.Decoder、custom UnmarshalJSON/UnmarshalXML、mapstructure weak typing、plugin/config loaders、interface{} polymorphic decode。
- [ ] Rust 项目已检查 serde dynamic structures、bincode、rmp-serde、postcard、custom Deserialize、plugin/config deserializers。

失败处理：项目语言存在但未检查对应 sink 时，不得声称 sink 搜索完成。

## F. 依赖与可达性门禁

- [ ] 依赖存在和项目调用分开记录。
- [ ] 项目调用和输入来源分开记录。
- [ ] source 到 sink 调用链有文件、函数、行号或搜索命令证据。
- [ ] 签名、加密、HMAC、CSRF、权限、租户、schema、白名单、safe loader、长度和来源限制已记录。
- [ ] 依赖存在但无调用标记 dependency-only。
- [ ] 有调用但无不可信输入标记 not reachable。
- [ ] 有可疑路径但未动态验证标记 candidate。
- [ ] 安全控制阻断标记 blocked。

失败处理：状态降级，不得把依赖存在写成漏洞。

## G. 动态验证门禁

- [ ] 每个 candidate 有验证目标。
- [ ] 每个 candidate 有正向样本。
- [ ] 每个 candidate 有负向样本。
- [ ] 每个 candidate 有阻断样本或无阻断说明。
- [ ] 每个 candidate 有 marker 或替代观测方式。
- [ ] 每个 candidate 有运行命令。
- [ ] 每个 candidate 有观测位置。
- [ ] 每个 candidate 有清理命令。
- [ ] 本地动态验证命令、请求、日志、marker 均已记录。

失败处理：缺失项补齐；无法执行时保持 candidate。

## H. confirmed 门禁

- [ ] 有不可信输入 source。
- [ ] 有反序列化 sink。
- [ ] 有 source 到 sink 调用链。
- [ ] 有本地动态验证。
- [ ] 有无害 marker。
- [ ] 有正向样本。
- [ ] 有负向样本。
- [ ] 有阻断样本或无阻断说明。
- [ ] 有日志或断言。
- [ ] 有清理动作。
- [ ] 有修复建议。
- [ ] 有回归测试建议。

失败处理：任一项缺失，confirmed 降级为 candidate 或 blocked/not reachable/dependency-only。

## I. 隐藏暴露面门禁

- [ ] remember-me cookie 已检查。
- [ ] session store 已检查。
- [ ] password reset token 已检查。
- [ ] email verification token 已检查。
- [ ] OAuth state/binding token 已检查。
- [ ] webhook 重放数据已检查。
- [ ] admin import 已检查。
- [ ] backup restore 已检查。
- [ ] workflow/rule/report template 已检查。
- [ ] plugin/theme/extension installer 已检查。
- [ ] metadata parser 已检查。
- [ ] YAML/XML/properties 配置导入已检查。
- [ ] cache warming 已检查。
- [ ] job retry/dead-letter/failed job 已检查。
- [ ] audit replay/event sourcing replay 已检查。
- [ ] database serialized column 已检查。
- [ ] ORM converter/message converter/RPC codec 已检查。
- [ ] GraphQL scalar/variables 已检查。
- [ ] WebSocket init payload 已检查。
- [ ] internal admin-only API 已检查。
- [ ] CLI maintenance command 已检查。
- [ ] SSR/server action 参数绑定已检查。
- [ ] content-type confusion 已检查。
- [ ] file extension 与 magic header 不一致已检查。
- [ ] base64/gzip/zip 包裹后的 serialized blob 已检查。
- [ ] 签名验证前先解析对象已检查。

失败处理：漏项进入补测清单，不得写覆盖完成。

## J. 交付门禁

- [ ] 输出执行摘要。
- [ ] 输出暴露面总表。
- [ ] 输出依赖与框架风险映射。
- [ ] 输出每个问题详情。
- [ ] 输出证据清单。
- [ ] 输出修复建议。
- [ ] 输出降级清单。
- [ ] 输出补测清单。
- [ ] 输出漏报追查清单。
- [ ] 输出强制自我反查。
- [ ] 工程化补强未伪装成原文。
- [ ] 未虚构命令、日志、marker、截图、行号、请求结果。
