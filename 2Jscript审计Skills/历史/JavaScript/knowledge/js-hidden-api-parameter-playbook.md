# JS 隐藏接口与隐藏参数专项 Playbook

1. 从 JS/HAR/Source Map 中提取 API 候选。
2. 从 router/component/菜单/i18n/feature flag 映射触发页面。
3. 从 TypeScript/interface/zod/yup/protobuf/OpenAPI/GraphQL variables 提取参数。
4. 从后端 route/controller/DTO/model/validator/ORM schema 提取接受字段。
5. 比较前端实际传参、UI 可控参数、schema 暗示参数、后端接受字段、HAR 真实参数。
6. 对 backend-only、UI-hidden、readonly、disabled、role/tenant 相关字段做非破坏性最小化 replay。
7. 未有请求响应差异前，全部保持 candidate-only 或 needs_review。
