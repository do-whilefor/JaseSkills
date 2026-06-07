# 本机授权安全审计工作流

## 1. 授权边界

只处理用户明确授权的本机目录、本机靶场、本机开源测试项目和本 Skills 包。动态验证默认使用 fixture、demo app、mock service、local replay。外部真实目标、破坏性写入、凭证滥用、横向移动、持久化和真实数据获取均禁止。

## 2. 静态审计

运行 `tools/js_asset_extractor.py`、`tools/route_extractor.py` 与现有 detector。静态结果只能标记 `STATIC_CANDIDATE` 或 `needs_review`，不得直接写成 confirmed。

## 3. 动态验证

动态状态必须使用：`STATIC_CANDIDATE`、`DYNAMIC_ATTEMPTED`、`DYNAMIC_CONFIRMED`、`DYNAMIC_BLOCKED`、`DYNAMIC_INCONCLUSIVE`、`NOT_TESTED`、`UNSAFE_TO_TEST`。缺 Playwright、浏览器、Burp 或本机服务时，必须记录 runtime missing。

## 4. 证据保存

所有 finding 必须绑定 source line、request/response、HAR、截图、命令输出或 replay id。缺证据时只允许进入人工复核队列。

## 5. 报告生成

报告必须区分 candidate、confirmed、inconclusive。`tools/quality_gate.py` 阻断无证据 confirmed、无 request/response dynamic finding、无 source line code-level finding。
