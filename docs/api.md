# API 合约

所有响应为 JSON。除健康检查和登录外均须登录。学生 API 从会话确定 student_id；`/api/admin/*` 由服务端检查管理员角色。

## 公共与登录

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/health | 服务状态 |
| POST | /api/login | `{username,password,role}` |
| GET | /api/me | 当前账户；学生包含 student 资料 |
| POST | /api/logout | 清除该账户会话 |
| GET | /api/catalog?q=&category=&available=1 | 馆藏检索 |
| GET | /api/books/{id} | 书目及全部副本详情 |

## 学生

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/student/overview | 学生资料及借阅/预约统计 |
| GET | /api/student/loans | 当前与历史借阅 |
| POST | /api/student/loans/{id}/renew | 续借 14 天 |
| GET | /api/student/reservations | 本人的预约 |
| POST | /api/student/reservations | `{book_id}` 加入队列 |
| DELETE | /api/student/reservations/{id} | 取消 waiting/ready 预约 |
| GET | /api/student/study-room-slots?date=YYYY-MM-DD | 返回指定日期的 8 个 study rooms × 14 个小时 slots（08:00–22:00）；只允许今天或明天。每个 slot 返回 `room_no`、`slot_start`、`status`（`expired`/`booked`/`available`）和 `reserved_student_uid` |
| GET | /api/student/study-room-bookings | 返回当前学生未来的 study-room bookings |
| POST | /api/student/study-room-slots/{id}/reserve | 预约一个小时的 slot |
| DELETE | /api/student/study-room-slots/{id}/reserve | 取消自己的 slot 预约 |

Study-room booking 每位学生每天最多两个小时；只有 `available` slot 可以预约，预约前端会要求确认。

## 图书管理员

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/admin/dashboard | 管理统计 |
| GET | /api/admin/libraries | 分馆下拉数据 |
| GET | /api/admin/students | 学生及借阅数 |
| GET/POST | /api/admin/books | 查询/新增书目 |
| PUT/DELETE | /api/admin/books/{id} | 编辑/删除书目 |
| GET/POST | /api/admin/copies | 查询/新增副本 |
| PUT/DELETE | /api/admin/copies/{id} | 编辑/删除副本 |
| GET | /api/admin/loans?active=1 | 借阅记录 |
| POST | /api/admin/checkout | `{student_no,barcode,loan_days}` |
| POST | /api/admin/loans/{id}/return | 办理归还 |
| GET | /api/admin/reservations | 全部预约队列 |

错误使用 400 参数错误、401 未登录、403 权限不足、404 不存在、409 业务或数据库冲突、500 内部错误；正文至少包含 `{error}`。
