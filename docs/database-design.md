# 数据库设计

## 设计重点

书目与实体副本必须分开。一本书的 ISBN、书名、出版社属于 `books`；每一本真正能被借出的实体书有独立条码、分馆、书架和状态，属于 `book_copies`。因此 `loans.copy_id` 指向实体副本，而 `reservations.book_id` 指向书目。

## 表与职责

| 表 | 主键与重要字段 | 职责 |
|---|---|---|
| accounts | id，username UNIQUE，role | 登录账户及角色 |
| students | id，account_id UNIQUE，student_no UNIQUE | 学生借阅身份和借阅上限 |
| sessions | token，account_id FK | 8 小时登录会话 |
| libraries | id，name UNIQUE | 分馆资料 |
| books | book_id，isbn UNIQUE，title | 书目版本；`book_id` 是系统主键 |
| authors | id，name UNIQUE | 规范化作者名称 |
| book_authors | (book_id, author_id) | 书目与作者的多对多关系 |
| book_copies | id，barcode UNIQUE，book_id FK | 实体副本、馆藏地和流通状态 |
| loans | id，copy_id FK，student_id FK | 借出、到期、归还和续借历史 |
| reservations | id，student_id FK，book_id FK | 书目预约队列 |
| study_room_slots | id，room_no，slot_start，status，reserved_student_uid | 今天/明天 8 个 study rooms 的 08:00–22:00 每小时 slot；`status` 为 `expired`、`booked` 或 `available` |

## 基数

- Account 1 — 0..1 Student：管理员账户没有学生资料。
- Account 1 — 0..N Session。
- Book M — N Author，通过 BookAuthor 分解。
- Book 1 — 0..N BookCopy。
- Library 1 — 0..N BookCopy。
- Student 1 — 0..N Loan；BookCopy 1 — 0..N Loan，历史可多条，但同时最多一条有效借阅。
- Student 1 — 0..N Reservation；Book 1 — 0..N Reservation。
- Student 1 — 0..N StudyRoomSlot：`reserved_student_uid` 为空表示可预约，非空表示已被该学生预约。

## 规范化

模型满足课程项目需要的 3NF 分解：

- 作者没有作为逗号字符串存入 books，而是拆为 authors 和 book_authors。
- 分馆名称与位置只存于 libraries，副本只保存 library_id。
- 借阅不会复制书名、学号或馆名，通过外键连接获取。
- 同一本书的多个实体副本不会重复 ISBN、出版社和描述。

## 完整性与事务

- `one_active_loan_per_copy` 是部分唯一索引，限制一个副本同时只有一条 `returned_at IS NULL` 的借阅。
- `one_open_reservation_per_student_book` 防止学生对同一书目重复提交 waiting/ready 预约。
- CHECK 约束限制角色、状态、续借次数、出版年份和借阅时间顺序。
- reserved 副本必须填写 `reserved_for_student_id`；其他状态不得填写。
- 借出和归还使用 `BEGIN IMMEDIATE`，使检查与更新处于同一写事务，避免两个管理员同时借出同一副本。
- `study_room_slots` 通过 `(room_no,slot_start)` 唯一约束保证一个房间的同一小时只有一个 slot；预约用事务把 `status` 从 `available` 更新为 `booked` 并写入 `reserved_student_uid`，避免两个学生抢到同一小时。过去的时间自动标记为 `expired`。

## 状态

副本：`available → borrowed → available`。若归还时有预约，则进入 `reserved`；被队首学生借走后进入 `borrowed`。管理员可把空闲副本设为 `maintenance`。

预约：`waiting → ready → fulfilled`；学生也可以从 waiting 或 ready 变为 cancelled。取消 ready 预约时，系统释放副本并继续分配给下一位。
