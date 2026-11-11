# 项目说明

本目录汇总数据库建模、ER 图、架构、API、SQL 示例和验证资料。

- [ER 图（PNG）](er.png) 与 [矢量图（SVG）](er.svg)，可编辑源码 [er.mmd](er.mmd)
- [数据库设计与字段说明](database-design.md)：实体、属性、关系、键、约束与文本演员名单的取舍
- [系统架构说明](architecture.md)：前后端、API 与数据库操作流程
- [API 合约](api.md)
- [SQL 增删改查示例](queries.sql)
- [项目计划](planning.md) 与 [验证记录](verification.md)
- [漏斗城市筛选页面预览](filter-preview.png)

城市保存在场馆的 `city` 文本字段；整份演员名单保存在具体场次的 `cast_text` 文本字段。本目录说明该简化模型的查询能力与规范化取舍。
