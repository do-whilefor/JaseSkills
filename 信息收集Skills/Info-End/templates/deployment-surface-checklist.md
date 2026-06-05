# 部署信息只读检查模板

用于覆盖 Docker、compose、Kubernetes、CI/CD、Nginx、Apache、Caddy、Traefik、Supervisor、systemd 等部署信息。该模板只产生候选，不直接产生信息暴露结论。

| 类型 | 文件/位置候选 | 只读检查点 | 输出状态 |
|---|---|---|---|
| Docker/Compose | Dockerfile、compose*.yml、docker-compose*.yml | ports、volumes、env_file、environment、networks、healthcheck | 候选 |
| Kubernetes | k8s/、deploy/、helm/、*.yaml | Ingress、Service、ConfigMap、Secret 名称、env、volumeMounts | 候选 |
| CI/CD | .github/workflows、.gitlab-ci.yml、Jenkinsfile、circleci、azure-pipelines | artifact、env name、build path、deploy URL、runner hint | 候选 |
| Nginx/Apache/Caddy/Traefik | nginx.conf、httpd.conf、Caddyfile、traefik*.yml | server_name、proxy_pass、root、alias、headers、basic auth hint | 候选 |
| Supervisor/systemd | supervisord.conf、*.service | ExecStart、WorkingDirectory、EnvironmentFile、User、ports hint | 候选 |

输出字段：编号、类型、文件、线索、脱敏摘要、是否运行态可验证、下一步 Skill、不可报告原因。
