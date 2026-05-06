# 秋海棠新种数据库网站上线执行方案（MVP→完整版）

## 0. 执行目标
- 4 周内上线可运营 MVP：可浏览、可检索、可审核、可推送。
- 8–10 周扩展为完整版本：覆盖全属知识库、多语言与开放 API。
- 质量目标：可持续更新、版权可追溯、数据可核验、运行可观测。

## 1. 总体架构（静态优先、动态增强）

### 1.1 前台（高性能内容站）
- 技术：Next.js + TypeScript + ISR
- 页面：
  - 首页（统计、近 7 天更新、地图概览）
  - 列表页（关键词+多维筛选）
  - 详情页（学名/文献/分布/媒体/审核信息）
  - 地图页（聚合点、筛选联动）
  - 昨日新增页（按日期归档）

### 1.2 后台（规范化数据库 + 审核流）
- 技术：Postgres（Supabase 托管）
- 模块：
  - 录入、编辑、审核、合并重复、批量导入
  - 审核流：`candidate -> provisional -> verified -> archived`
  - 角色：管理员/编辑/审核员/投稿用户

### 1.3 自动化（抓取 + 核验 + 推送）
- 抓取三层：
  - 发现层：期刊/DOI 元数据（4–6 小时）
  - 核验层：命名学与分布核验（新增后立即）
  - 媒体层：图版入口与许可复核（每日）
- 推送：每日 8 点（按业务时区），支持邮件与 Telegram 起步。

---

## 2. 数据模型（核心表）

### 2.1 业务核心
- `species`：物种主事实表（学名、作者、发表日期、状态、可信度）
- `source_documents`：文献来源（article/pdf/news/social）
- `external_refs`：权威系统引用（IPNI/POWO/Tropicos/JSTOR/DOI）
- `media_assets`：媒体策略（hosted/proxied/linked_only/card_only）
- `occurrences`：分布坐标（含模糊化级别）

### 2.2 运营与审核
- `submissions`：用户投稿与审核
- `subscriptions`：订阅对象与时区偏好
- `digests`：日报快照
- `delivery_logs`（建议补充）：多渠道投递记录与重试状态

### 2.3 关键约束
- DOI 唯一（可空）；slug 唯一
- 公开 API 仅返回 `verified`
- 坐标敏感控制：`exact/blurred/region_only`
- 媒体展示必须先判断 `display_policy`

---

## 3. 抓取与可信度评分

### 3.1 来源优先级
1. 一级：Taiwania、Phytotaxa、Crossref、POWO/WCVP、IPNI、Tropicos
2. 二级：JSTOR Global Plants、标本馆、机构新闻
3. 三级：社媒/论坛（仅候选线索，必须人工审核）

### 3.2 去重顺序
1. DOI 完全匹配
2. 学名规范化匹配
3. 标题 trigram 相似度
4. 同期刊同日期 + 地理近邻
5. 人工合并确认

### 3.3 可信度建议分
- DOI + 文章页 + PDF：+40
- IPNI 命名匹配：+20
- POWO/Tropicos 名录或分布匹配：+20
- 有图版/标本入口：+10
- 仅社媒线索：+0（默认 candidate）
- 与既有记录冲突：-30

### 3.4 自动发布阈值（建议）
- `score >= 80` 且无冲突：可进入“待审核快速通道”
- `60 <= score < 80`：常规审核
- `< 60`：保持 candidate

---

## 4. 图片与版权策略（硬规则）

### 4.1 默认策略
- **链出优先，托管例外**：许可不清即 `linked_only`
- 托管仅限：自拍、明确授权、明确允许再分发来源

### 4.2 前台表现
- `hosted`：站内缩略图 + 原图
- `linked_only`：来源卡片 + 图题/页码 + 去原站
- `card_only`：仅信息卡，不展示图像

### 4.3 合规台账字段
- 来源站名、原 URL、图号/页码、版权方、许可、是否允许派生、热链策略、核验时间

---

## 5. API 设计（首批）

### 5.1 公开查询
- `GET /api/species`
- `GET /api/species/{slug}`
- `GET /api/species/{slug}/media`
- `GET /api/species/{slug}/sources`
- `GET /api/species/{slug}/occurrences`
- `GET /api/digests?date=YYYY-MM-DD`
- `GET /api/facets`

### 5.2 投稿与后台
- `POST /api/submissions`
- `POST /api/admin/imports/csv`
- `POST /api/admin/imports/notion-sync`
- `POST /api/admin/reconcile`
- `POST /api/admin/publish`
- `POST /api/admin/revalidate`

---

## 6. 8 周排期（可直接执行）

## 第 1 周（基础冻结）
- 冻结字段字典、状态流、版权等级
- 清洗 Excel/CSV，建立导入脚本
- 建库与初始迁移，完成样例导入

## 第 2 周（前台 MVP）
- 首页/列表/详情/地图
- 搜索筛选（FTS + pg_trgm）
- 基础 SEO（metadata/sitemap/robots）

## 第 3 周（后台 MVP）
- 登录与权限
- CRUD、审核队列、导入导出
- 媒体策略 UI（display_policy 显式化）

## 第 4 周（自动化 + 首次上线）
- 接入 2–3 个一级来源
- 去重与评分
- “昨日新增”日报 + 邮件/Telegram 二选二通道

## 第 5–6 周（增强）
- 扩充来源与核验适配器
- 加强日志、监控、失败重试
- 用户投稿与审核优化

## 第 7–8 周（完整化）
- 全属扩展、专题页、多语言字段
- API 文档、运维手册、备份演练

---

## 7. 质量门禁（Definition of Done）

### MVP 上线门禁（全部满足）
1. 公开端可稳定访问（首页/列表/详情/地图/昨日新增）
2. 后台可完成从候选到核验发布闭环
3. 版权策略生效（许可不清不托管）
4. 抓取成功率 >= 95%（按周）
5. 日报准点率 >= 98%（按业务时区窗口）
6. 关键操作有审计日志，数据库可恢复演练通过

### 运行指标（首月建议）
- 新增候选处理时长 P95 <= 48h
- 重复入库率 <= 1%
- 外链失效率 <= 3%
- 详情页 TTFB P95 <= 800ms（命中缓存）

---

## 8. 风险与应对
- 图片侵权：默认 `linked_only` + 24h 下架机制
- 学名误判：staging + 三方核验 + 终审
- 推送时差：UTC 调度 + 时区换算
- 外链失效：保留 DOI + 文章页 + 来源页三层入口
- 误操作：软删除 + 快照 + 回滚脚本

---

## 9. 立即启动清单（今天就能做）
1. 建立仓库目录（`/docs`, `/db`, `/scripts`, `/apps/web`, `/apps/admin`）
2. 完成 schema v1 与迁移脚本 v1
3. 录入 10 条样本做端到端演练
4. 打通第一个日报通道（邮件）
5. 设置周例会看板：来源成功率、审核堆积、投递成功率

