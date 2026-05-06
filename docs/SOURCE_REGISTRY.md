# 信息采集登记（Authority Source Registry）

更新日期：2026-04-24（UTC）

## 一级来源（已确认入口）

1. Crossref REST API
- 文档：https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- API 根地址：https://api.crossref.org/
- 过滤器文档：https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/
- 用途：DOI 元数据、全文链接线索、发布时间、期刊信息

2. Tropicos Web Services
- 文档入口：https://services.tropicos.org/help
- 示例（图像）：https://services.tropicos.org/help?method=GetNameImagesXml
- 用途：Name Images / References / Distributions / Specimens 等程序化访问

3. IPNI（命名学核验）
- 说明页面：https://www.us.ipni.org/about
- RDF 示例：https://www.ipni.org/n/30117681-2/rdf
- 用途：学名、作者、命名学记录与对账

## 采集脚本
- `scripts/collect_sources.py`
  - 默认：实时请求 Crossref API。
  - 代理模式遇到 `Tunnel connection failed: 403` 时，会自动尝试一次直连回退。
  - 直连模式：`--direct`（忽略 HTTP(S)_PROXY，适用于允许直连的环境）。
  - 受限环境：`--offline-sample` 生成标准化模板数据。

## 输出文件
- `data/crossref_begonia_candidates.json`
