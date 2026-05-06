# DB 使用说明

## 目标
`schema_v1.sql` 是可直接执行的 PostgreSQL 初版结构，重点解决：
- 数据质量约束（枚举、范围检查、唯一约束）
- 查询性能（状态/时间/全文/模糊索引）
- 审核与投递流水可追溯

## 执行方式
```bash
psql "$DATABASE_URL" -f db/schema_v1.sql
```

## 关键改进点（相对初稿）
1. 将状态字段改为 enum type，避免字符串漂移。
2. 增加 `gen_random_uuid()` 默认值（`pgcrypto`）。
3. 为核心表增加 `updated_at` 自动触发器。
4. `species` 增加 `search_tsv` 生成列 + GIN 索引（支持全文检索）。
5. 坐标与尺寸增加范围校验，降低脏数据概率。
6. 增加若干唯一约束与高频查询索引（订阅、投递、文献）。

## 注意事项
- 本 schema 未包含用户认证表（如 `users`），`submissions.assigned_to` 目前为预留字段。
- 若已在生产环境创建旧版同名对象，升级前请先评估迁移脚本（ALTER / backfill）再执行。
