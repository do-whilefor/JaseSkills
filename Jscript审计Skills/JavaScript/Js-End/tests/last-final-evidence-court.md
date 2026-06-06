# 终极反向审判 / 证据法庭报告

## 0. 判决摘要

- 修正后总分：27/100。
- 最终判定：未达到世界顶级 JS 安全渗透测试 Skills 标准。
- 降级原则：无文件证据即未证实；只有文档即 doc-only；只有 regex/候选即 candidate-only；无 Playwright/Burp/HAR 即未动态验证；无 role/tenant replay 即缺少多角色多租户验证。

## 1. 运行证据扫描

| 项目 | 结果 |
| --- | --- |
| 文件数 | 153 |
| Skill 文件数 | 16 |
| 缺失必需文件 | 无 |
| 禁用缓存/临时文件 | 无 |
| AST backend | missing/fake-ready risk |
| Source Map parser | partial/doc-only |
| Playwright/Burp/HAR bridge | 未动态验证 |
| Role/Tenant replay | 缺少 role/tenant replay |
| Detector harness | candidate-only/doc-only |
| Schema validator | 证据不可强校验 |
| Report mapping | 无法闭环到报告 |
| Dashboard | 展示层伪闭环 |
| Knowledge/template checker | 知识库/模板接入未强证据化 |
| Real OSS replay | 缺少真实 OSS replay |

## 2. 逐条审判前两轮重要结论
| 原结论 | 当时依据 | 真实文件证据 | 真实测试证据 | 是否可能幻觉 | 是否高估能力 | 修正后结论 | 必须补充的证据 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| package_self_check.py: ok，所以包结构健康 | 命令输出显示 ok | scripts/package_self_check.py | 测试不足 | 是 | 是 | 部分证实。包卫生检查通过，但不等于工程能力 ready。 | 增加 workflow 调用链、runtime backend、真实 replay、report generator、dashboard 读取真实产物的测试证据 |
| verify_extreme_review_assets.py: ok，极限评审资产完整 | 校验脚本返回 ok | scripts/verify_extreme_review_assets.py, 12-js-skills-extreme-reviewer/SKILL.md | 测试不足 | 是 | 是 | 资产存在证实；能力 ready 未证实。 | 增加每项 JS 收集/审计/漏洞链的执行级测试 |
| verify_second_pass_assets.py: ok，二次反审资产完整 | 校验脚本返回 ok | scripts/verify_second_pass_assets.py, 13-js-skills-second-pass-reverse-auditor/SKILL.md | 测试不足 | 是 | 是 | 二次反审承载能力部分证实；真实漏洞发现能力仍 missing/partial。 | 增加 detector harness、dynamic replay、schema validation、report mapping 测试 |
| 修正后总分 32/100 足够严格 | second_pass_reverse_audit.py 输出 | scripts/second_pass_reverse_audit.py, tests/last-second-pass-review.json | tests/last-second-pass-review.md | 中 | 是 | 需要按失败惩罚规则再次下调并写明扣分证据。 | 增加 final_court_score_penalty_rules.json 和命令输出 |
| 知识库和漏洞模板未删除，原有 Skills 能力未削弱 | 压缩包中仍有 knowledge/templates 目录 | knowledge/, templates/ | 测试不足 | 是 | 是 | 文件存在部分证实；调用链和能力未削弱未证实。 | 新增 knowledge/template index checker、hash baseline、before/after 对比 |
| skill_trigger_tester.py: ok，路由可用 | 触发测试通过 | scripts/skill_trigger_tester.py, tests/trigger-test-cases.json, scripts/skill_dispatcher.py | tests/last-trigger-test-output.jsonl | 中 | 是 | 路由规则部分证实；执行链路未证实。 | 新增 e2e workflow runner，校验 route → script → manifest → quality gate → report → dashboard |
| 无 __pycache__ / .pyc / .tmp / .bak / .swp | 压缩包检查和 self_check | scripts/package_self_check.py | 测试不足 | 是 | 是 | 证实为包卫生项，不应计入 JS 审计能力分。 | 保留为卫生 gate，不扩大解释 |
| 没有把 AST/runtime/detector 伪装成 ready | 二次反审结果中 parser_backend_evidence/runtime_bridge_evidence/detector_evidence 为空 | tests/last-second-pass-review.json | 测试不足 | 是 | 是 | 部分证实；仍需全包 grep 文档一致性。 | 新增 final evidence court grep 一致性检查和伪 ready 表 |

## 3. JS 收集漏报事故模拟
| 漏报事故 | 当前为什么漏 | 可能严重漏洞 | 缺失能力 | 修复文件 | 新增测试 | 验收标准 |
| --- | --- | --- | --- | --- | --- | --- |
| 登录后才加载的 chunk | 缺少登录态浏览器采集器和 trace/HAR 资产账本 | 账号接管入口、hidden API、token refresh abuse | playwright_role_chunk_collector.py | scripts/playwright_role_chunk_collector.py | fixtures/final-court-js-collection/authenticated-chunk/ | role-login replay 输出 HAR、trace、chunk hash、manifest |
| 管理员角色才加载的 chunk | 缺少 admin/user role diff replay | admin endpoint 越权、退款/封禁接口滥用 | role_chunk_diff_collector.py | scripts/role_chunk_diff_collector.py | fixtures/final-court-js-collection/admin-only-chunk/ | admin 与普通用户 chunk diff 产生 endpoint 差异证据 |
| 租户专属 chunk | 缺少 tenant A/B runtime diff | tenant-only API、BOLA、跨租户数据读取 | tenant_chunk_diff_collector.py | scripts/tenant_chunk_diff_collector.py | fixtures/final-court-js-collection/tenant-only-chunk/ | 至少两个租户 replay 输出 chunk/API 差异 |
| feature flag 触发的 chunk | 缺少 feature flag forced route discovery | 灰度 admin/internal endpoint、隐藏业务流 | feature_flag_chunk_collector.py | scripts/feature_flag_chunk_collector.py | fixtures/final-court-js-collection/feature-flag-chunk/ | feature flag 组合触发 chunk 并记录来源 |
| stale source map | 缺少旧构建 sourcemap 枚举和 freshness gate | 源码、secret、hidden API 泄露 | stale_sourcemap_collector.py | scripts/stale_sourcemap_collector.py | fixtures/final-court-js-collection/stale-sourcemap/ | 发现旧 map 并还原 sourcesContent/path |
| CDN 旧版本 JS | 缺少 CDN stale asset resurrection 检查 | 旧漏洞代码、已下线 endpoint、secret 残留 | cdn_stale_asset_collector.py | scripts/cdn_stale_asset_collector.py | fixtures/final-court-js-collection/cdn-stale-asset/ | 同 asset 多版本 hash 差异和历史 URL 证据 |
| Service Worker cache 旧资产 | 缺少 SW/Cache Storage runtime dump | 持久 XSS、旧 API、cache poisoning | service_worker_cache_collector.py | scripts/service_worker_cache_collector.py | fixtures/final-court-js-collection/sw-cache-old-assets/ | 导出 Cache Storage 资产账本 |
| Next.js build manifest | 缺少 _next/build-manifest 与 app-build-manifest 解析 | 未发现页面 chunk、server action/RSC 边界线索 | next_manifest_collector.py | scripts/next_manifest_collector.py | fixtures/final-court-js-collection/next-build-manifest/ | 解析 pages/app route 到 chunk 映射 |
| Vite manifest | 缺少 manifest.json/modulepreload 解析 | 动态 import endpoint、env 泄露 | vite_manifest_collector.py | scripts/vite_manifest_collector.py | fixtures/final-court-js-collection/vite-manifest/ | 解析 entry/imports/dynamicImports/css/assets |
| Webpack runtime chunk | 缺少 webpack runtime module id/chunk graph 解析 | 隐藏模块、异步路由、admin route | webpack_runtime_chunk_collector.py | scripts/webpack_runtime_chunk_collector.py | fixtures/final-court-js-collection/webpack-runtime/ | 还原 chunk id → URL → module 关系 |
| GraphQL persisted query | 缺少 persisted query hash discovery | hidden mutation、IDOR、tenant bypass | graphql_persisted_query_collector.py | scripts/graphql_persisted_query_collector.py | fixtures/final-court-js-collection/graphql-persisted-query/ | 提取 hash/query/mutation/variables 证据 |
| WebSocket schema | 缺少 WS message capture/schema inference | 跨用户消息读取、租户越权 | websocket_schema_collector.py | scripts/websocket_schema_collector.py | fixtures/final-court-js-collection/websocket-schema/ | 捕获消息 schema、auth header、tenant id |
| Electron preload bundle | 缺少 Electron ASAR/preload/ipc 枚举 | preload bridge RCE、任意文件读写 | electron_preload_collector.py | scripts/electron_preload_collector.py | fixtures/final-court-js-collection/electron-preload/ | 提取 preload、contextBridge、ipcRenderer 调用 |
| Browser extension content script | 缺少 extension manifest/content/background 采集 | 权限提升、token leak、externally_connectable abuse | extension_bundle_collector.py | scripts/extension_bundle_collector.py | fixtures/final-court-js-collection/browser-extension/ | 解析 manifest/content scripts/host_permissions |
| Mobile WebView bridge JS | 缺少 WebView bridge 名称和 native bridge 调用收集 | 移动端账号接管、任意调用 native 方法 | webview_bridge_collector.py | scripts/webview_bridge_collector.py | fixtures/final-court-js-collection/mobile-webview-bridge/ | 发现 window.* bridge、JSInterface、schema |
| WASM glue code | 缺少 wasm/js glue 和 imports/exports 解析 | unsafe parser、边界逻辑缺陷、文件处理漏洞线索 | wasm_glue_collector.py | scripts/wasm_glue_collector.py | fixtures/final-court-js-collection/wasm-glue/ | 输出 wasm import/export、glue sink、调用点 |
| 第三方 iframe postMessage JS | 缺少 iframe src 与 postMessage runtime 采集 | token leak、origin bypass、account takeover | iframe_postmessage_collector.py | scripts/iframe_postmessage_collector.py | fixtures/final-court-js-collection/iframe-postmessage/ | 记录 origin/source/data schema/sink |
| 支付/退款/优惠券业务 JS | 缺少业务域 chunk 标记和敏感流量 replay | 前端价格控制、退款滥用、优惠券逻辑绕过 | business_flow_js_collector.py | scripts/business_flow_js_collector.py | fixtures/final-court-js-collection/payment-refund-coupon/ | 敏感业务入口触发 chunk 和 API diff |
| 富文本/Markdown/文件预览 JS | 缺少 preview/editor/markdown renderer 资产聚类 | stored DOM XSS、mXSS、SVG/PDF preview XSS | richtext_preview_collector.py | scripts/richtext_preview_collector.py | fixtures/final-court-js-collection/richtext-preview/ | 提取 renderer、sanitizer、preview sink |
| localStorage/IndexedDB 敏感缓存 | 缺少浏览器 storage dump 与差异分析 | JWT/PII/tenant cache 泄露、跨标签 token leak | browser_storage_collector.py | scripts/browser_storage_collector.py | fixtures/final-court-js-collection/storage-sensitive-cache/ | 导出 local/session/IndexedDB/CacheStorage 证据 |

## 4. JS 审计伪能力拆穿
| 声称能力 | 真实实现 | 为什么是伪能力/半成品 | 会导致什么漏报 | 如何升级成真能力 | 验收测试 |
| --- | --- | --- | --- | --- | --- |
| AST 审计 | 未发现 scripts/js_ast_parser_backend.py、babel/ts/tree-sitter backend | 文档/矩阵声明多，真实 parser backend 缺失 | 混淆 wrapper、template literal endpoint、复杂 sink/source 漏报 | 新增 parser backend + AST snapshot fixture + backend availability check | fixtures/final-court-pseudo/ast-backend-missing.json |
| Source Map 解析 | 未发现 sourcemap_parser.py 或 sourcesContent/path mapping 强测 | 只记录 source map 点不等于解析原始源码 | secret、hidden API、monorepo path、server logic 泄露漏报 | 新增 sourcemap_parser.py，支持 sources/sourcesContent/sourceRoot | fixtures/final-court-pseudo/sourcemap-sourcescontent.json |
| endpoint resolver | 未发现 baseURL/env/template literal/URLSearchParams resolver | 关键词 endpoint 提取不是解析器 | 拼接 API、动态 host、租户路径漏报 | 新增 endpoint_resolver.py 和拼接用例 | fixtures/final-court-pseudo/template-literal-endpoint.json |
| auth-aware detector | 未发现 token/header/cookie/tenant flow resolver | 没有 auth flow 就不能判断权限边界 | client auth bypass、BOLA、WebSocket authz 漏报 | 新增 auth_context_resolver.py | fixtures/final-court-pseudo/auth-flow.json |
| source-sink dataflow | 未发现 CFG/DFG 或 source→transform→sink 输出 schema | 候选 sink 列表不是数据流 | DOM XSS、prototype pollution、postMessage chain 漏报 | 新增 js_dataflow_engine.py | fixtures/final-court-pseudo/source-sink-chain.json |
| DOM XSS detector | 未发现 source/sink/context/sanitizer model | sink grep 会产生误报并漏上下文 | stored DOM XSS、mXSS、sanitizer bypass 漏报 | 新增 dom_xss_semantic_detector.py | fixtures/final-court-pseudo/dom-xss-context.json |
| postMessage detector | 未发现 origin/source/data schema/sink 判定 | message 关键词不等于漏洞判断 | token leak、account takeover 漏报 | 新增 postmessage_origin_detector.py | fixtures/final-court-pseudo/postmessage-origin.json |
| GraphQL detector | 未发现 query/mutation/variables/permission diff | 提取 /graphql URL 不等于 GraphQL 安全审计 | hidden mutation、IDOR、tenant bypass 漏报 | 新增 graphql_operation_resolver.py | fixtures/final-court-pseudo/graphql-mutation-diff.json |
| WebSocket detector | 未发现 message schema/auth/tenant replay | 发现 ws URL 不等于鉴权审计 | 跨用户消息读取、租户越权漏报 | 新增 websocket_authz_replay.py | fixtures/final-court-pseudo/websocket-authz.json |
| dynamic validation | 未发现 Playwright/Burp/HAR bridge 和截图/请求响应证据 | 静态候选不能替代动态验证 | 所有需要复现的高危链均无法 verified | 新增 dynamic_evidence_bridge.py | fixtures/final-court-pseudo/dynamic-validation-missing.json |

## 5. 严重 JS 漏洞高危漏报清算
| 严重漏洞 | 当前覆盖状态 | 漏报原因 | 误报风险 | 动态验证缺口 | 证据链缺口 | 修复方案 |
| --- | --- | --- | --- | --- | --- | --- |
| Source Map 泄露源码 → hidden API | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：Source Map 泄露源码 → hidden API |
| Source Map 泄露源码 → secret | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：Source Map 泄露源码 → secret |
| JS hidden admin endpoint → 越权 | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：JS hidden admin endpoint → 越权 |
| JS role guard bypass | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：JS role guard bypass |
| JS tenant id diff → BOLA | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：JS tenant id diff → BOLA |
| GraphQL hidden mutation | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：GraphQL hidden mutation |
| GraphQL persisted query hash 枚举 | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：GraphQL persisted query hash 枚举 |
| WebSocket authz bypass | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：WebSocket authz bypass |
| postMessage token leak | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：postMessage token leak |
| OAuth redirect_uri/state/nonce/PKCE 缺陷 | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：OAuth redirect_uri/state/nonce/PKCE 缺陷 |
| JWT refresh abuse | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：JWT refresh abuse |
| Firebase/Supabase/S3/GCS/Azure 未授权读写 | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：Firebase/Supabase/S3/GCS/Azure 未授权读写 |
| DOM XSS | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：DOM XSS |
| stored DOM XSS | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：stored DOM XSS |
| mXSS | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：mXSS |
| prototype pollution | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：prototype pollution |
| DOM clobbering | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：DOM clobbering |
| Service Worker cache poisoning | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：Service Worker cache poisoning |
| CDN stale asset resurrection | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：CDN stale asset resurrection |
| CORS/JSONP chain | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：CORS/JSONP chain |
| Client-side open redirect → OAuth chain | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：Client-side open redirect → OAuth chain |
| CSP gadget chain | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：CSP gadget chain |
| Electron preload/IPC RCE | doc-only/missing-runtime | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：Electron preload/IPC RCE |
| Browser extension privilege escalation | doc-only/missing-runtime | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：Browser extension privilege escalation |
| WebView bridge account takeover | doc-only/missing-runtime | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：WebView bridge account takeover |
| dependency confusion | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：dependency confusion |
| npm postinstall/prepare malicious script | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：npm postinstall/prepare malicious script |
| frontend-only payment/refund/price control | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：frontend-only payment/refund/price control |
| upload validation bypass → server exploit chain | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：upload validation bypass → server exploit chain |
| WASM boundary parser flaw clue | candidate-only/doc-only | 缺少语义 detector、动态验证、role/tenant replay 或证据 manifest 强校验 | 高：没有上下文、授权、可达性和复现证据 | 未动态验证 | partial-template-only; not strongly proven | 新增 detector/replay/fixture/report mapping：WASM boundary parser flaw clue |

## 6. Skills 包结构工程验尸
| 工程问题 | 证据文件 | 为什么危险 | 影响的能力 | 修复方式 | 验收命令 |
| --- | --- | --- | --- | --- | --- |
| dashboard 缺失或未读取真实运行产物 | 未发现 dashboard_generator.py, 未发现 dashboard/ 目录 | 展示层无法证明 route→candidate→evidence→quality→report 闭环 | dashboard/report confidence | 新增 dashboard_generator.py 和 dashboard/index.html，读取 last-*.json | python scripts/dashboard_generator.py . |
| report generator 缺失 | templates/final-report.md 存在但未发现 report_generator.py | 模板存在会被误解为自动报告闭环 | report mapping | 新增 report_generator.py，强制从 manifest 和 quality gate 填充报告 | python scripts/report_generator.py . |
| schema 未被统一强校验 | schemas/*.schema.json 存在, 未发现统一 schema_validator.py | 证据字段可能漂移，无法复核 | evidence chain | 新增 schema_validator.py 并纳入 package_self_check | python scripts/schema_validator.py . |
| AST backend 缺失 | 未发现 js_ast_parser_backend.py, 未发现 babel/typescript/tree-sitter adapter | regex/candidate 被误用为语义审计 | JS semantic audit | 新增 parsers/js_ast_parser_backend.py 与 runtime availability check | python scripts/runtime_availability_check.py . --require ast |
| Source Map parser 缺失 | 未发现 sourcemap_parser.py | 无法还原 sourcesContent、sourceRoot、原始路径 | sourcemap audit | 新增 sourcemap_parser.py 和 stale sourcemap fixture | python scripts/sourcemap_parser.py fixtures/... |
| Playwright/Burp/HAR bridge 缺失 | 未发现 playwright_bridge.py、burp_har_bridge.py、har_importer.py | 无法动态验证，verified 状态不可信 | dynamic validation | 新增 dynamic_evidence_bridge.py | python scripts/dynamic_evidence_bridge.py --selftest |
| role/tenant replay 缺失 | 未发现 role_tenant_replay.py, fixtures 仅为合成占位 | 最容易漏报 BOLA/IDOR/admin chunk | serious vulnerability discovery | 新增 role_tenant_replay.py 和多账号 fixture contract | python scripts/role_tenant_replay.py --fixture fixtures/... |
| quality gate scorer 不足 | scripts/strict_quality_gate.py 存在但不覆盖 final_court P0 状态 | 无法按失败惩罚规则量化质量 | quality gate | 扩展 strict_quality_gate.py 读取 final_court_score_penalty_rules.json | python scripts/strict_quality_gate.py tests/last-final-evidence-court.json |
| knowledge/template 引用链未强制验证 | knowledge/ 和 templates/ 存在, 未发现 template_index_checker.py/knowledge_index_checker.py | 知识库存在可能被误判为已接入 | knowledge fidelity | 新增索引检查和 hash baseline | python scripts/knowledge_template_index_checker.py . |
| 真实 OSS replay 缺失 | 未发现 replay/real-oss/ | 合成 fixture 无法证明复杂框架覆盖 | engineering trust | 新增 replay/real-oss 合同与脱敏样本清单 | python scripts/replay_harness.py replay/real-oss |

## 7. 失败惩罚规则重新评分
| 评分项 | 原分数 | 惩罚规则 | 修正分数 | 扣分证据 |
| --- | --- | --- | --- | --- |
| Skills 包结构 | 7 | 无 dashboard/report/schema/index/e2e 强闭环，结构分不能代表能力 | 5 | scripts/package_self_check.py 只检查文件存在和缓存 |
| 信息收集能力 | 6 | 未证明子域/URL/HAR/Burp/Playwright 与 JS 审计闭环 | 3 | 缺少 info_js runtime bridge 和 replay |
| JS 收集能力 | 8 | 没有 Source Map 真实解析，JS 收集最高 70%；同时缺 role/tenant runtime chunk | 5 | 缺 sourcemap_parser.py、role_chunk_diff_collector.py |
| JS AST / 语义审计能力 | 5 | 没有真实 AST backend，JS 审计最高不得超过 40%；当前 detector 也缺失 | 3 | 未发现 Babel/TS/tree-sitter backend |
| 严重 JS 漏洞发现能力 | 7 | 没有多角色/多租户 replay，严重漏洞发现最高 60%；没有 detector 继续扣分 | 4 | 缺 role_tenant_replay.py 与 severe detector harness |
| 动态验证与证据链 | 3 | 没有 Playwright/Burp/HAR 动态证据，动态验证最高 30% | 2 | 缺 playwright_bridge.py、burp_har_bridge.py、har_importer.py |
| 测试与回放 | 4 | 没有完整 positive/negative/blocked/review 样本和真实 OSS replay，测试最高 40% | 2 | fixtures 多为占位，缺 replay/real-oss |
| 知识库与模板保真度 | 4 | 存在不等于索引/调用；缺 hash baseline 和 index checker | 3 | 缺 knowledge_template_index_checker.py |

## 8. 不可辩解 P0 清单
| P0 编号 | 问题 | 证据 | 严重后果 | 修改文件 | 新增文件 | 新增测试 | 验收标准 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0-COURT-01 | 真实 JS AST backend 缺失 | 未发现 Babel/TypeScript/tree-sitter adapter | 复杂 wrapper、route、sink/source 全部可能漏报 | 03-js-source-sink-authz-graph/SKILL.md, scripts/strict_quality_gate.py | parsers/js_ast_parser_backend.py, scripts/runtime_availability_check.py | fixtures/final-court-p0/ast-positive.js, fixtures/final-court-p0/ast-negative.js | 运行 availability check 和 AST fixture 后输出 AST node/sink/source 证据 |
| P0-COURT-02 | Source Map parser 缺失 | 未发现 sourcemap_parser.py | 源码、secret、hidden API、monorepo path 泄露漏报 | 05-js-frontend-build-exposure/SKILL.md | scripts/sourcemap_parser.py | fixtures/final-court-p0/sourcemap-with-sourcesContent.map | 输出 sources/sourcesContent/sourceRoot/hash/path 账本 |
| P0-COURT-03 | Playwright/Burp/HAR 动态证据桥缺失 | 未发现 playwright_bridge.py/burp_har_bridge.py/har_importer.py | 静态候选被误报为 verified，证据链不可复核 | 07-js-dynamic-validator/SKILL.md, 08-js-evidence-manifest-gate/SKILL.md | scripts/dynamic_evidence_bridge.py, schemas/dynamic-evidence.schema.json | fixtures/final-court-p0/har-sample.json | 生成 HAR、截图、request/response、trace 证据字段 |
| P0-COURT-04 | role/tenant replay 缺失 | 未发现 role_tenant_replay.py | admin chunk、tenant chunk、BOLA/IDOR 大量漏报 | 07-js-dynamic-validator/SKILL.md | scripts/role_tenant_replay.py, replay/contracts/role-tenant-replay.yaml | fixtures/final-court-p0/role-tenant-diff.json | 至少输出 user/admin/tenantA/tenantB endpoint/chunk diff |
| P0-COURT-05 | 严重 JS 漏洞 detector harness 缺失 | 未发现 detectors/ 或 detector registry | 30 类严重漏洞只能候选化，无法稳定发现 | 06-js-high-risk-candidate-hunter/SKILL.md | detectors/js_detector_registry.py, detectors/dom_xss_semantic_detector.py, detectors/graphql_operation_detector.py | fixtures/final-court-p0/detector-positive.json | 每个 detector 输出 evidence id、confidence、blocked/review/verified 状态 |
| P0-COURT-06 | schema 强校验未统一接入 | schemas 存在但缺统一 validator | manifest/report 字段漂移，证据不可强校验 | 08-js-evidence-manifest-gate/SKILL.md, scripts/package_self_check.py | scripts/schema_validator.py | fixtures/final-court-p0/schema-invalid.json | 无效 manifest 必须失败并列出字段路径 |
| P0-COURT-07 | report mapping 缺失 | 模板存在但缺 report_generator.py | 漏洞无法从证据闭环进入报告，报告污染风险高 | 10-js-final-report/SKILL.md | scripts/report_generator.py, data/report_mapping.json | fixtures/final-court-p0/report-mapping.json | candidate/review/verified 状态在报告中分区输出 |
| P0-COURT-08 | dashboard 未读取真实产物 | 未发现 dashboard_generator.py 或 dashboard/ | 展示层伪闭环，无法追踪 route→evidence→quality | docs/CAPABILITY_INDEX.md | scripts/dashboard_generator.py, dashboard/index.html | fixtures/final-court-p0/dashboard-input.json | dashboard 从 last-final-evidence-court.json 生成页面 |
| P0-COURT-09 | positive/negative/blocked/review 样本不足 | fixtures 多为 README 或单个 JSON 占位 | 误报/漏报无法量化 | tests/regression-test-plan.md | fixtures/final-court-matrix/positive, fixtures/final-court-matrix/negative, fixtures/final-court-matrix/blocked, fixtures/final-court-matrix/needs-review | tests/final-court-fixture-matrix.json | 每类严重漏洞至少四类样本各 1 个 |
| P0-COURT-10 | 知识库/模板保真度未强证据化 | 缺 hash baseline、knowledge/template index checker | 可能误删、误路由或模板孤岛 | docs/DOCUMENT_MAPPING_MATRIX.md | scripts/knowledge_template_index_checker.py, data/knowledge_template_hash_baseline.json | fixtures/final-court-p0/template-index-conflict.json | before/after hash 和索引引用一致 |
| P0-COURT-11 | 真实 OSS replay 缺失 | 未发现 replay/real-oss/ | 复杂框架覆盖率不可证实 | tests/regression-test-plan.md | replay/real-oss/README.md, scripts/replay_harness.py | replay/contracts/real-oss-replay.schema.json | 至少 10 个授权/本地 OSS replay 合同通过 |
| P0-COURT-12 | 伪 ready 文档一致性 gate 缺失 | 缺 fake_ready_grep_gate.py | README/SKILL.md 可能把 doc-only 写成 ready | docs/QUALITY_GATE_SPEC.md | scripts/fake_ready_grep_gate.py | fixtures/final-court-p0/fake-ready-doc.md | 任何无 backend 证据的 ready 表述导致 CI 失败 |

## 9. 最终结论

1. 当前 Skills 是否达到世界顶级标准：未达到世界顶级 JS 安全渗透测试 Skills 标准。
2. 差距最大的 10 个点：真实 JS AST backend；Source Map sourcesContent 解析；Playwright/Burp/HAR 动态证据桥；role/tenant replay；严重漏洞 detector harness；schema 强校验；report mapping；dashboard 读取真实产物；positive/negative/blocked/review 样本矩阵；真实 OSS replay。
3. 当前最危险的 10 个伪 ready：AST 审计声明；Source Map 支持声明；endpoint resolver 声明；auth-aware 声明；dataflow 声明；DOM XSS detector 声明；postMessage detector 声明；GraphQL detector 声明；WebSocket detector 声明；dynamic validation 声明。
4. 当前最容易漏报的 10 类 JS 严重漏洞：Source Map 泄露源码 → hidden API；Source Map 泄露源码 → secret；JS hidden admin endpoint → 越权；JS role guard bypass；JS tenant id diff → BOLA；GraphQL hidden mutation；GraphQL persisted query hash 枚举；WebSocket authz bypass；postMessage token leak；OAuth redirect_uri/state/nonce/PKCE 缺陷。
5. 当前最容易造成 Claude 幻觉的 10 个位置：README 能力总览；SKILL.md 中的愿景语句；data/*.json 矩阵被误当实现；templates 被误当 detector；fixtures README 被误当 replay；schema 存在被误当校验；quality gate 文档被误当 scorer；dashboard 目标被误当真实展示；knowledge 存在被误当接入；route test 被误当端到端执行。
6. 第一轮需要撤回/降级的结论：资产完整不等于能力 ready；路由测试通过不等于执行闭环；模板存在不等于报告闭环；知识库存在不等于知识接入；包卫生 ok 不等于 JS 审计质量。
7. 第一轮必须下调的分项：JS AST/语义审计；严重 JS 漏洞发现；动态验证与证据链；测试与 replay；报告/dashboard 闭环。

### 7 天修复路径
- Day 1: 建立 runtime_availability_check、fake_ready_grep_gate、schema_validator，阻止伪 ready。
- Day 2: 接入 Babel/TypeScript/tree-sitter AST backend，完成 AST positive/negative fixture。
- Day 3: 实现 Source Map parser，覆盖 sourcesContent/sourceRoot/stale map。
- Day 4: 实现 endpoint/auth/tenant resolver 与 role/tenant diff contract。
- Day 5: 实现 Playwright/HAR bridge 和 request/response/screenshot evidence manifest。
- Day 6: 为 30 类严重 JS 漏洞建立 detector registry 和四象限样本。
- Day 7: 接入 report generator、dashboard、真实 OSS replay、knowledge/template hash baseline。

### 保真证明
- 修复后必须运行 knowledge_template_index_checker.py 与 hash baseline，对比新增包前后 knowledge/templates 文件列表与 SHA256。
- 修复后必须运行 package_self_check、trigger tester、schema validator、detector fixtures、dynamic replay dry-run、report/dashboard generation，并对比原始 Skill 路由链未减少。
