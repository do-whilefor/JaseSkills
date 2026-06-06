#!/usr/bin/env python3
from __future__ import annotations
import json
fingerprints = [
  '目录结构与语言识别','工作原理剖析','参数与输入面检查','代码知识图谱','配置文件分析','依赖与供应链分析','框架级漏洞挖掘','高危 JS 漏洞重点挖掘','前端 JS 深挖','动态验证计划','证据标准','最终输出格式','环境确认','候选漏洞归档','验证优先级排序','单漏洞验证模板','三次复现','反证要求','证据 manifest','覆盖率反思','小众路径','链式漏洞重组','误报审查','动态验证质量审计'
]
print(json.dumps({'fingerprint_count': len(fingerprints), 'fingerprints': fingerprints}, ensure_ascii=False, indent=2))
