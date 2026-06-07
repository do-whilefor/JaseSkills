# DASHBOARD_SPEC.md

静态 dashboard 展示链路：

`Route → Handler → AuthZ → Parameter → Data Flow → Sink → Candidate → Evidence → Quality Gate → Report`

## 输入

- `evidence/*.json` 或 `evidence_manifest.json`
- `route_graph.json`
- `js_findings.json`
- `quality_results.json`
- `report_index.json`

## 页面区块

1. 资产总览：语言、框架、配置、依赖、入口点数量。
2. 暴露面：路由/API/GraphQL/WebSocket/RPC/上传下载/任务/CLI。
3. 候选漏洞：按 23 类、风险、状态、证据完整度聚合。
4. 证据链：代码证据、动态证据、负样本、复现次数。
5. 质量门槛：评分、缺失项、误报原因。
6. 报告映射：candidate_id 到报告章节和修复建议。

生成：

```bash
python scripts/dashboard_generator.py --evidence evidence_manifest.json --out dashboard/index.html
```
