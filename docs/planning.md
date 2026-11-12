# 港大图书馆课程系统实施计划

## 目标

完成一个可本地运行的图书馆 Web 系统，明确区分学生与图书管理员权限，并用 SQLite 持久化展示关系数据库设计、事务和约束。

## 当前实施范围

- 学生：登录、检索馆藏、查看每本书的可借副本数、预约无可借副本的书、查看/取消预约、查看当前借阅、续借、查看借阅历史。
- 图书管理员：仪表盘、书目 CRUD、副本 CRUD、学生列表、按学号办理借出、归还、查看全部借阅及预约记录。
- 系统：HttpOnly 会话、服务端角色检查、参数化 SQL、外键/唯一/检查约束、借出/归还事务、演示数据和 API 测试。
- 不包含：真实 HKU Portal 单点登录、罚款支付、馆际互借、邮件通知、RFID、自助机和生产部署。

## 架构

- 前端：原生 HTML/CSS/JavaScript 单页界面，同一套页面按角色显示不同导航。
- 后端：Python 3.10+ 标准库 `ThreadingHTTPServer`，提供 JSON API 和静态文件。
- 数据库：SQLite `data/library.db`；业务表包括 accounts、students、libraries、books、authors、book_authors、book_copies、loans、reservations、sessions。
- 文件：封面使用 CSS 书封或 URL，不在数据库存二进制。

## API 与关键规则

- 所有业务 API 必须登录；`/api/admin/*` 仅管理员可访问。
- 学生只能操作自己账户关联的借阅和预约。
- 同一副本至多存在一条未归还借阅；同一学生对同一书目至多存在一条等待预约。
- 办理借出使用 `BEGIN IMMEDIATE`；原子检查副本、学生借阅上限和预约优先权，再新增 loan 并更新副本状态。
- 归还在同一事务内关闭借阅并把副本设为 available；若存在预约队列，则设为 reserved 并指向最早预约。
- 续借仅允许未逾期、未达到续借次数上限且没有其他学生等待的记录。

## 实施顺序

1. 替换数据库 schema 与种子数据，建立约束和索引。
2. 重写后端认证、学生 API、管理员 API 与事务逻辑。
3. 重写前端登录、学生门户和管理员工作台。
4. 更新 API、架构、数据库、ER 和运行说明。
5. 重写集成测试，执行 Python/JavaScript 检查和真实浏览器流程。

## 验证

- `python3 -m unittest discover -s tests -v`
- `python3 -m py_compile server.py`
- `node --check static/app.js`
- 使用临时数据库启动服务，分别走通学生与管理员浏览器流程。

本项目不是 agent 系统，因此不需要 agent benchmark。

## 2026-11-12 English UI and account switching

- Translate all user-facing browser copy, status labels, confirmation dialogs and API error messages into English.
- Store demo student names in English and migrate existing local demo rows to `Kayan Chan` and `Li Wenhao` during startup.
- Add a persistent `My Account` action at the bottom of both role sidebars.
- Add an account page showing the active identity and role.
- Allow only an authenticated librarian to switch to the fixed student demo account. Students cannot switch to the librarian role without logging in with librarian credentials.
- Verify the role transition through API integration tests and a real browser flow.

## Study room booking

- Add one `study_room_slots` table with 8 rooms × 14 hourly slots (08:00–22:00) for each of today and tomorrow.
- Store `room_no`, `slot_start`, `status` (`expired`, `booked`, `available`) and `reserved_student_uid` on each slot row.
- Expose student-only list, reserve, and cancel endpoints; only `available` slots may be booked.
- Render a date-switching 8×14 booking matrix inside the student's Study Room Booking page.
