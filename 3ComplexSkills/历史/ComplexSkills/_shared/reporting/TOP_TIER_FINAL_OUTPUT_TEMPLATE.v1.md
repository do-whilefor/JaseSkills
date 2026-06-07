# Top Tier Final Output Template v1

Final reports must use this structure when the task asks for world-class authorized vulnerability hunting, JS lazy-loading review or browser dynamic validation review.

1. 执行摘要
   - maturity score;
   - AI lazy-loading problem status;
   - real browser interaction status;
   - vulnerability hunting capability;
   - dynamic validation capability;
   - authorized practical readiness.

2. Skills 包结构审查
   - file;
   - issue;
   - impact;
   - repair;
   - priority;
   - blocking status.

3. 信息收集能力审查
   - covered;
   - uncovered;
   - hidden attack surface;
   - repair plan.

4. JS 收集与审计审查
   - static JS assets;
   - lazy assets;
   - browser-triggered assets;
   - source map;
   - service worker;
   - router;
   - API client;
   - WebSocket / GraphQL;
   - uncovered reason.

5. 真实浏览器交互矩阵
   - page;
   - action;
   - new chunk;
   - new API;
   - evidence;
   - coverage status.

6. 严重漏洞候选列表
   - vulnerability type;
   - file path;
   - code position;
   - route/API;
   - role/tenant condition;
   - source;
   - sink;
   - guard;
   - bypass hypothesis;
   - dynamic validation steps;
   - evidence;
   - confidence;
   - confirmed status.

7. 已确认漏洞列表
   - minimal reproduction;
   - non-destructive request;
   - expected result;
   - actual result;
   - HAR/screenshot/log/code evidence;
   - impact;
   - fix;
   - variant expansion.

8. 漏洞拓展结果
   - same-root-cause variants;
   - same API family;
   - same permission model;
   - same tenant model;
   - same file-processing chain;
   - same JS exposure chain;
   - possible vulnerability chain.

9. 反思与自我追责
   - not executed;
   - inferred only;
   - evidence gaps;
   - likely false negatives;
   - likely false positives;
   - human review;
   - missing tools;
   - next run priority.

10. 修复后的顶级执行方案
    - skill files to add or modify;
    - rules to modify;
    - scripts to add;
    - fixtures to add;
    - evidence schema to add;
    - dashboard panels to add;
    - browser interaction enforcement;
    - anti-lazy and anti-fake-completion controls.
