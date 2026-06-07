# Final Review

本清单用于完成一轮验证后的反向审判。默认立场：所有结论都可能证据不足，必须逐条复核、降级或补测。

## A. 审判已有结论

对每个 confirmed / candidate / false positive 检查：

- [ ] 是否真的执行了动态请求。
- [ ] 是否真的创建了 marker 文件。
- [ ] 是否真的证明读取到了 marker。
- [ ] 是否真的证明写入到了 marker 测试目录。
- [ ] 是否真的证明文件落点越界。
- [ ] 是否真的有正向、负向、blocked 三类对照。
- [ ] 是否真的测试了不同角色。
- [ ] 是否真的测试了不同租户。
- [ ] 是否真的测试了隐藏参数。
- [ ] 是否真的测试了前端未暴露但后端接受的字段。
- [ ] 是否真的检查了上传后的二次访问链路。
- [ ] 是否真的检查了预览、转换、缩略图、缓存、临时文件。
- [ ] 是否真的检查了后台异步 worker。
- [ ] 是否真的排除了误报。
- [ ] 是否存在把 candidate 误写成 confirmed。

降级规则：凡缺少动态证据的，降级为 candidate 或 not tested。

## B. 反查遗漏入口

- [ ] avatar / logo / icon / image / media / attachment。
- [ ] import / export / backup / restore。
- [ ] preview / thumbnail / render / convert。
- [ ] template / theme / plugin / extension。
- [ ] report / invoice / pdf / document。
- [ ] locale / lang / i18n。
- [ ] log / debug / trace。
- [ ] admin-only 文件管理功能。
- [ ] 富文本编辑器上传接口。
- [ ] Markdown / HTML / PDF 渲染中的资源读取。
- [ ] GraphQL mutation / query 中的 file、path、key 字段。
- [ ] WebSocket / RPC 中的文件读取或上传消息。
- [ ] 老版本 API、隐藏 API、废弃路由。
- [ ] 测试接口、开发接口、debug 接口。
- [ ] 对象存储代理下载接口。
- [ ] CDN / static proxy / media proxy。
- [ ] 根据 URL 生成预览的功能。
- [ ] 导入压缩包后自动解压的功能。
- [ ] 用户自定义模板、主题、插件上传。
- [ ] 后台配置中可修改存储路径的功能。

## C. 用偏门思路重测上传

- [ ] 文件名规范化差异。
- [ ] 大小写扩展名。
- [ ] 双扩展名。
- [ ] 尾随点和尾随空格。
- [ ] Unicode 正规化。
- [ ] URL 编码和双重编码。
- [ ] 路径分隔符混用。
- [ ] multipart 中 filename 与额外 name/path 字段冲突。
- [ ] JSON body 中隐藏 path/key/folder 字段。
- [ ] 上传接口参数覆盖服务端默认路径。
- [ ] 分片上传合并阶段绕过。
- [ ] 断点续传 session 污染。
- [ ] 上传后重命名逻辑绕过。
- [ ] 压缩包解压路径逃逸。
- [ ] 软链接或归档链接逃逸，且只能在 marker 目录中安全验证。
- [ ] 图片 / PDF / Office 解析器产生临时文件后的二次读取。
- [ ] 上传文件被复制到多个目录后，其中一个目录权限错误。
- [ ] 临时目录清理失败导致可下载。
- [ ] 文件去重 hash 导致跨用户复用。
- [ ] 同名文件覆盖 marker 文件，且禁止覆盖真实文件。

## D. 用偏门思路重测读取

- [ ] id 与 path 同时存在时后端信任谁。
- [ ] key 与 url 同时存在时后端信任谁。
- [ ] 合法 ID 搭配非法 path。
- [ ] 合法租户 ID 搭配其他租户 objectKey。
- [ ] 预览接口绕过下载权限。
- [ ] 缩略图接口绕过原图权限。
- [ ] 转换接口绕过源文件权限。
- [ ] 导出接口读取任意模板。
- [ ] 日志接口读取任意 marker。
- [ ] 本地化语言包读取 marker。
- [ ] 静态资源代理读取 marker。
- [ ] 对象存储 fallback 到本地路径。
- [ ] 缓存命中导致跨用户读取。
- [ ] 软删除文件仍可读取。
- [ ] 临时导出文件无权限校验。
- [ ] 文件分享链接权限过宽。
- [ ] 预签名链接过期校验错误。
- [ ] 只校验文件 ID 不校验 owner。
- [ ] 只校验租户不校验用户。
- [ ] 只校验前端按钮不校验后端接口。

## E. 反查依赖风险

必须基于项目实际依赖回答：

- [ ] 哪些依赖参与 multipart 解析。
- [ ] 哪些依赖参与路径拼接。
- [ ] 哪些依赖参与压缩包解压。
- [ ] 哪些依赖参与图片、PDF、Office 解析。
- [ ] 哪些依赖参与静态文件服务。
- [ ] 哪些依赖参与对象存储。
- [ ] 哪些依赖参与导入导出。
- [ ] 哪些依赖存在历史路径穿越、任意读取、解压逃逸、临时文件泄露风险。
- [ ] 项目是否错误封装了这些依赖。
- [ ] 是否存在 wrapper 封装后绕过官方安全用法。

## F. 反查代码结构

- [ ] Controller / route。
- [ ] Service。
- [ ] Middleware。
- [ ] Guard / policy。
- [ ] DTO / schema。
- [ ] Storage adapter。
- [ ] File utility。
- [ ] Background job。
- [ ] Cron task。
- [ ] Import/export module。
- [ ] Admin module。
- [ ] Test-only route。
- [ ] Deprecated route。
- [ ] Static serving config。
- [ ] Nginx / Apache / reverse proxy config。
- [ ] Docker volume mount。
- [ ] Environment config。
- [ ] CI / test fixture 中暴露的路径。
- [ ] 前端 JS 中隐藏接口。
- [ ] sourcemap 中隐藏接口。

## G. 重新生成动态验证矩阵

| endpoint | method | auth role | tenant | user | parameter | file operation | marker target | expected safe result | actual result | evidence | severity | status | next action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  | confirmed / candidate / false positive / blocked / not tested |  |

## H. 严厉降级规则

只要出现以下任一情况，必须降级：

- [ ] 没有请求证据。
- [ ] 没有响应证据。
- [ ] 没有 marker 证据。
- [ ] 没有文件系统前后状态。
- [ ] 没有对照组。
- [ ] 没有权限矩阵。
- [ ] 没有租户矩阵。
- [ ] 没有说明为什么不是预期功能。
- [ ] 没有证明影响范围。
- [ ] 没有可复现步骤。

## I. 最终交付必须回答

- [ ] 刚刚漏掉了什么。
- [ ] 刚刚误判了什么。
- [ ] 刚刚证据不足的地方。
- [ ] 刚刚没有动态验证的地方。
- [ ] 刚刚没有覆盖的偏门入口。
- [ ] 刚刚没有覆盖的依赖风险。
- [ ] 刚刚没有覆盖的二次链路。
- [ ] 新增的验证计划。
- [ ] 新增的 confirmed 漏洞。
- [ ] 被降级的漏洞。
- [ ] 仍然无法确认的 candidate。
- [ ] 下一步最优先补测的 10 个点。
