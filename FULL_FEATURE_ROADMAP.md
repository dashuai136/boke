# 功能齐全版开发清单（逐项落地）

> 目标：从已可运行 MVP 进入“功能齐全版”，按模块逐项交付。

## A. 公开前台（P0）
- [x] 首页统计与最近更新
- [x] 物种列表检索与筛选
- [x] 物种详情（学名/文献/媒体/分布）
- [x] 昨日新增页
- [x] 地图页（MVP JSON 点位）
- [ ] 地图升级为 MapLibre/Leaflet 矢量底图 + 聚类
- [ ] 多语言字段展示（zh/en）

## B. 数据与 API（P0）
- [x] SQLite MVP schema 与初始化脚本
- [x] 公开 API：species/media/sources/occurrences/digests/facets/submissions
- [ ] Postgres 生产环境迁移脚本（SQLite -> Postgres）
- [ ] API 鉴权与速率限制

## C. 后台审核（P0）
- [x] 投稿提交
- [x] 后台审核状态更新
- [ ] 角色权限（管理员/编辑/审核员）
- [ ] 审核日志与操作留痕
- [ ] 批量导入导出

## D. 抓取与去重（P1）
- [x] Crossref 采集（含 403 直连回退）
- [ ] Taiwania/Phytotaxa 适配器
- [ ] DOI/学名/标题相似度去重流水线
- [ ] 可信度评分自动化

## E. 推送与订阅（P1）
- [ ] 每日 8 点日报生成（按业务时区 + entered_at）
- [ ] 邮件通道
- [ ] Telegram 通道
- [ ] 投递日志与失败重试

## F. 生产化与安全（P0）
- [x] systemd 常驻配置
- [x] supervisor 备选配置
- [x] Nginx 反代 + TLS 模板
- [ ] 备份/恢复演练脚本
- [ ] 监控告警（健康检查 + 错误率）

## 里程碑
- M1（已完成）：MVP 本地可运行 + API + 审核基础流
- M2（进行中）：生产守护部署 + 域名公网接入
- M3（待完成）：抓取扩展 + 推送通道 + 权限体系
