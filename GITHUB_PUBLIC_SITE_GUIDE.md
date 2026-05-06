# 挂载到 GitHub 并形成公网站点（实操）

> 你要的目标是“代码在 GitHub + 对外可访问网站”。
> 本仓库已内置 Docker、Render 配置、GitHub Actions。

## 1) 推送到 GitHub

```bash
git remote add origin git@github.com:<YOUR_ORG_OR_USER>/<YOUR_REPO>.git
# 或 HTTPS
git remote add origin https://github.com/<YOUR_ORG_OR_USER>/<YOUR_REPO>.git

git branch -M main
git push -u origin main
```

## 2) 在 Render 创建公网服务（推荐，最省事）
1. 登录 Render -> New + -> Web Service。
2. 选择刚刚的 GitHub 仓库。
3. Render 会识别 `render.yaml` + `Dockerfile`。
4. 完成后会生成公网地址：
   - `https://<your-service>.onrender.com`

## 3) 配置自动部署（GitHub Push 自动发布）
1. 在 Render 服务里复制 Deploy Hook URL。
2. 在 GitHub 仓库设置 secret：
   - 名称：`RENDER_DEPLOY_HOOK`
   - 值：Render 的 Deploy Hook URL
3. 之后每次 push 到 `main` 将触发 `.github/workflows/deploy-render.yml` 自动发布。

## 4) 域名绑定（变成你的正式公网域名）
1. 在 Render 服务 -> Settings -> Custom Domains 添加：
   - 例如 `flora.example.org`
2. 在 DNS 平台添加 CNAME（按 Render 提示）。
3. 等待证书签发后访问：
   - `https://flora.example.org`

## 5) 验收清单
- 首页：`/`
- 列表：`/species`
- API：`/api/species?page_size=1`
- 投稿：`/submit`
- 后台：`/admin`

## 6) 重要说明
- 当前 SQLite 数据文件在容器本地，重建容器可能丢失。
- 生产建议切换到 Postgres（本仓库已有 `db/schema_v1.sql`）。
