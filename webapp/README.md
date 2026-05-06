# 秋海棠数据库网站（MVP 可运行版）

## 功能
- 首页统计 + 最新记录
- 物种列表（搜索/筛选）
- 详情页（媒体/来源/分布）
- 地图页（点位展示）
- 昨日新增页（按 entered_at）
- 投稿页（写入 submissions）
- 后台页（审核 submissions）
- API：`/api/species`、`/api/species/<slug>`、`/api/species/<slug>/media`、`/api/species/<slug>/sources`、`/api/species/<slug>/occurrences`、`/api/digests`、`/api/facets`、`/api/submissions`

## 启动
```bash
python3 webapp/init_db.py
python3 webapp/app.py
```

打开：`http://127.0.0.1:8080`

## 说明
- 当前为 **Python 标准库 + SQLite** 的 MVP 落地版，无第三方依赖，便于在受限环境直接跑通。
- 生产可替换到 Postgres（已有 `db/schema_v1.sql`）。
- 长期后台守护、域名与公网接入请看 `DEPLOYMENT_GUIDE.md`（systemd/supervisor/nginx/TLS）。
- 功能齐全版逐项实施清单见 `FULL_FEATURE_ROADMAP.md`。
- GitHub 挂载并形成公网站点（Render + 自动部署）见 `GITHUB_PUBLIC_SITE_GUIDE.md`。
