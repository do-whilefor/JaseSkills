# Release Notes: 2026.06.06-clean1

本版本是 Js-End 的清理发布版，目标是保留原有知识库与漏洞模板，同时移除运行产物和缓存，降低压缩包冗余。

## 已保留

- `knowledge/`：8 个知识库文件。
- `templates/`：18 个漏洞、证据、报告与复核模板。
- `00` 至 `23` 全部子 Skill。
- JS 收集、API 参数建模、隐藏参数、runtime evidence、GraphQL/WebSocket、sourcemap、service worker、framework parser、dashboard、quality gate 相关脚本。

## 已清理

- 上次 fixture 运行目录：`tests/js-top-tier-last-run/`。
- 环境检查输出：`reports/env-check/`。
- 临时日志、缓存、系统垃圾文件。

## 仍然坚持的降级策略

此包提供可执行框架与可验收标准，但不会把未导入真实授权目标证据的结论标记为 ready。真实项目运行后，只有满足 evidence manifest、role/tenant、backend acceptance、HAR/trace/screenshots/request-response 证据链，严重漏洞才允许从 candidate 升级。
