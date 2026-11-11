# API 合约

同源 JSON；登录成功后发送 HttpOnly/SameSite=Strict Cookie，8 小时过期。每次 API 从数据库查询账户角色，前端角色选项不能授予权限。无公开管理员注册接口。

| 方法 | 路径 | 行为 |
|---|---|---|
| GET | /api/health | 服务/数据库类型（不需登录） |
| POST | /api/login | {username,password,role}；角色和账号必须匹配 |
| GET | /api/me | 当前登录用户 id/username/role |
| POST | /api/logout | 注销该账号所有会话 |
| GET | /api/cities | 城市列表 |
| GET | /api/calendar?month=2026-06&city=1&city=2 | 指定月份、多城市的已发布开票轮次 |
| GET | /api/runs/1 | 批次详情，含 sales/channels、performances/cast |
| GET | /api/admin/{table} | 管理员查询完整记录列表 |
| POST | /api/admin/{table} | 新增，返回 201 与 {id} |
| PUT | /api/admin/{table}/{id} | 全字段更新，返回 {ok:true} |
| DELETE | /api/admin/{table}/{id} | 删除，返回 {ok:true} |
| POST | /api/admin/upload | {data:"图片的base64正文"}，返回 {url}；PNG/JPEG ≤4MB |

{table} 白名单：cities,venues,productions,runs,performances,actors,characters,casts,sale_rounds,channels,sale_channels。写入正文须包含数据字典对应表除 id 外的所有字段。日期 YYYY-MM-DD，时间 YYYY-MM-DDTHH:mm，中国标准时间。published 0/1。kind priority/general。

错误：400 参数问题，401 未登录/登录失败，403 权限不足/来源不匹配，404 记录或接口不存在，409 数据库约束冲突，500 内部错误。错误正文 {error,detail?}。SQL 表名和列名来自白名单；业务值通过 ? 占位符绑定。

例：POST /api/admin/sale_rounds
```json
{"run_id":1,"opens_at":"2026-11-08T12:00","kind":"general","note":"加场开票"}
```
删除这条新增轮次后，对应日历记录也会消失；数据不是前端数组或 localStorage 模拟。

本地课程实现，不含公网生产服务的 TLS、登录限速、用户注册、重置密码、审计与备份管理。服务仅监听 127.0.0.1。部署需在标准应用服务器/反向代理后补齐相应设施和 Secure Cookie。
