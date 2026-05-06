# 秋海棠新种数据库项目（Begonia New Species Hub）

本仓库包含可运行 MVP、采集脚本、数据库模型、部署配置与运营文档。

## 快速开始（本地）
```bash
python3 webapp/init_db.py
python3 webapp/app.py
```
访问：`http://127.0.0.1:8080`

## 文档导航
- 项目文档总览：`docs/PROJECT_DOCS_INDEX.md`
- 可行性与边际：`docs/FEASIBILITY_AND_BOUNDARIES.md`
- MVP 执行方案：`IMPLEMENTATION_PLAN.md`
- 周执行清单：`WEEKLY_EXECUTION_CHECKLIST.md`
- 功能齐全版路线：`FULL_FEATURE_ROADMAP.md`
- 服务器部署（systemd/supervisor/nginx）：`DEPLOYMENT_GUIDE.md`
- GitHub -> 公网站点：`GITHUB_PUBLIC_SITE_GUIDE.md`

## 当前状态（2026-05-06）
- 已有：可运行 Web MVP、SQLite 模式、基础 API、投稿与审核流、采集脚本、CI、部署模板。
- 未完成：生产数据迁移到 Postgres、角色权限、自动推送、权威源扩展与去重评分自动化。

## 说明
- 当前线上化建议优先采用 Postgres（`db/schema_v1.sql`）作为生产主库。
- SQLite 版本用于本地演示和快速联调。
