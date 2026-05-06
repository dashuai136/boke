# 项目文档总览（整理版）

> 目的：降低文档分散度，明确“看哪里、先做什么、上线缺什么”。

## 1. 战略与范围
- `IMPLEMENTATION_PLAN.md`：MVP->完整版总体方案、里程碑与质量门禁。
- `FULL_FEATURE_ROADMAP.md`：模块化任务清单与当前完成状态。
- `docs/FEASIBILITY_AND_BOUNDARIES.md`：可行性结论、技术/运营边际、风险红线。

## 2. 执行与协作
- `WEEKLY_EXECUTION_CHECKLIST.md`：周度可执行任务。
- `docs/SOURCE_REGISTRY.md`：权威来源清单与接入说明。

## 3. 数据与后端
- `db/schema_v1.sql`：Postgres 生产主库模型（推荐生产使用）。
- `db/README.md`：schema 执行与迁移注意事项。
- `webapp/schema.sql`：SQLite MVP 模型（本地演示）。

## 4. 运行与部署
- `webapp/README.md`：本地启动说明。
- `DEPLOYMENT_GUIDE.md`：systemd/supervisor/nginx/TLS 运维部署。
- `GITHUB_PUBLIC_SITE_GUIDE.md`：GitHub 挂载与公网站点发布（Render）。
- `deploy/scripts/healthcheck.sh`：在线健康检查脚本。

## 5. 自动化与质量
- `.github/workflows/ci.yml`：测试 CI。
- `.github/workflows/deploy-render.yml`：Render 自动部署触发。
- `tests/test_collect_sources.py`：采集脚本测试。
- `tests/test_webapp.py`：Web MVP 接口与页面烟测。

## 建议阅读顺序
1) `README.md`
2) `docs/FEASIBILITY_AND_BOUNDARIES.md`
3) `FULL_FEATURE_ROADMAP.md`
4) `DEPLOYMENT_GUIDE.md` / `GITHUB_PUBLIC_SITE_GUIDE.md`（按部署目标二选一）
