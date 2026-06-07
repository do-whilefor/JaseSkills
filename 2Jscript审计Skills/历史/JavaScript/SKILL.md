---
name: JavaScript
description: "Evidence-first JavaScript collection, analysis, API modeling, runtime evidence, and authorized security audit skill pack."
---

# JavaScript

这是集合型 Claude Skill 的顶层入口，适用于授权范围内的 JS / 前端 / Node.js / Web 项目安全审计。

## 调度顺序

1. 先读取 `00-js-master-dispatcher/SKILL.md`。
2. 涉及授权边界、证据门槛、报告结论时，必须读取 `01-js-scope-evidence-quality-gate/SKILL.md` 与 `08-js-evidence-manifest-gate/SKILL.md`。
3. 涉及隐藏接口、隐藏参数、前端不传但后端接受参数、真实浏览器懒加载、多角色/多租户 replay、严重 JS 漏洞验证时，必须读取 `16` 至 `20` 号 Skill。
4. 涉及 HAR/trace/screenshots、GraphQL/WebSocket runtime replay、schema 对齐、sourcemap 还原、service worker cache、framework build artifact、OSS replay 或环境自检时，必须读取 `21` 至 `23` 号 Skill。

## 证据规则

静态发现只能进入 candidate。没有代码证据、请求/响应、HAR/trace/screenshot、role/tenant 对比、backend acceptance、evidence manifest 和质量门禁通过结果时，不得把任何严重漏洞写成 verified。

## 保留目录

本清理版保留原有 `knowledge/` 知识库、`templates/` 漏洞模板、`data/` 规则数据、`schemas/`、`fixtures/`、`scripts/`、`tests/` 与全部子 Skill。清理仅移除缓存、运行产物、版本/发布说明和一次性更新记录，不删除知识库或漏洞模板。

## Windows 入口

优先使用：

```powershell
npm run windows:check
npm run windows:validate
powershell -ExecutionPolicy Bypass -File .\tools\windows\validate.ps1
```

Windows 动态录制只有在本机执行并真实生成 HAR、trace.zip、screenshot、DOM snapshot、console log、request/response、GraphQL/WebSocket/postMessage frame 文件后，才能计入 runtime evidence。
