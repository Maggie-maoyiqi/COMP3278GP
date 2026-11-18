# COMP3278 Library Portal — copy-ready slide content

This is the text to paste into the slides. The **Screenshot to take** lines are production instructions, not slide text. The SQL below follows the current project code and schema. Keep the slide text in English; the short Chinese instructions explain what to capture. Total speaking time, including the video, is **5:00**. The video itself is **1:40**, below the two-minute limit.

## Before making slides

1. Start the app with `cd COMP3278GP && python3 server.py`, then open `http://127.0.0.1:8765/`.
2. Use the student demo account to capture Search, Study Room Booking, and My Bookings. Use the librarian demo account to capture Books, Circulation, and Requests. Crop the browser chrome; leave the page title and relevant data visible.
3. For SQL slides, type the short snippets below into the PPT as editable code. Do not screenshot an entire source file. Highlight the matching UI element with a numbered callout.
4. Capture screens before changing demo data for the video. The app's student book requests and study-room bookings are different operations.

## Slide 1 — Title (0:00–0:15)

**Paste on slide**

> COMP3278 Library Portal
> A database-backed library service for students and librarians
> Group members: [replace with your names]

**Visual:** One clean screenshot of the student Search page, cropped to the header, category filter, and a few book cards.

**Say:** “Our portal brings book discovery, loans, book requests and study-room reservations together. The librarian view manages physical copies and circulation.”

## Slide 2 — Functionality and interface (0:15–0:40)

**Paste on slide**

> **Student** — Search books, renew loans, request unavailable books, and reserve study rooms.
> **Librarian** — Maintain book and copy records, check books out and in, and review requests.
> **Design choice** — Book requests target a title; loans target one physical copy.

**Screenshot to take:** 左右并排放两张：学生 Search 页的 category 下拉框与书卡；管理员 Circulation 页的 checkout/return 区域。不要放登录页。

**Say:** “Students and librarians have separate screens and permissions. The catalogue record and a physical copy are separate because one title may have several borrowable copies.”

## Slide 3 — ER diagram and keys (0:40–1:20)

**Paste on slide**

> **BOOK** (`book_id` PK, `isbn` UNIQUE) → **BOOK_COPY** (`book_id` FK): one title, many copies.
> **BOOK** ↔ **AUTHOR** through **BOOK_AUTHOR**: many-to-many.
> **LOAN** references a student and a physical copy; **RESERVATION** references a student and a book.
> **STUDY_ROOM_SLOTS** uses `(room_no, slot_start)` as a unique room-and-hour key.

**Screenshot to take:** 截取项目 `docs/er.svg` 中 BOOK、BOOK_COPY、AUTHOR、LOAN、RESERVATION 的关系并放左侧；右侧用简洁文本框补充 Study Room Slots。注意：提供的设计文档画了 STUDY_ROOM → ROOM_SLOT → BOOKING 三张表，但当前实现是单张 `study_room_slots` 表，展示时必须如实说明，别把三张表当成已实现。

**Say:** “The internal book ID is stable, while ISBN is a unique business identifier. Copy status belongs to each physical copy. Room and hour are unique together, which prevents duplicate slot rows.”

## Slide 4 — Key SQL ①: catalogue search (1:20–1:50)

**Paste on slide**

> **Search books by category and availability**

```sql
SELECT b.book_id, b.title, b.category,
       COUNT(DISTINCT bc.id) AS total_copies,
       COUNT(DISTINCT CASE WHEN bc.status = 'available'
                           THEN bc.id END) AS available_copies
FROM books b
LEFT JOIN book_copies bc ON bc.book_id = b.book_id
WHERE b.category = ?
GROUP BY b.book_id
HAVING available_copies > 0;
```

**Comment boxes to paste beside code**

> ① `b.category = ?` applies the selected category.
> ② `COUNT(DISTINCT bc.id)` counts physical copies without duplicates.
> ③ `HAVING` keeps only books with an available copy.

**Screenshot to take:** 学生 Search 页面选择一个分类，并勾选 “Available only”，截图要同时显示筛选控件与结果书卡。建议选 Computer Science；截图前确认书卡 category 与选择一致。

**Say:** “The same page combines category filtering with copy availability. We group by the book ID so the result is one row per title.”

## Slide 5 — Key SQL ②: study-room booking (1:50–2:25)

**Paste on slide**

> **Reserve an available room-hour, at most two per student per day**

```sql
BEGIN IMMEDIATE;
SELECT id, status, slot_start
FROM study_room_slots
WHERE id = ?;
SELECT COUNT(*) FROM study_room_slots
WHERE reserved_student_uid = ?
  AND status = 'booked'
  AND substr(slot_start, 1, 10) = ?;
UPDATE study_room_slots
SET status = 'booked', reserved_student_uid = ?
WHERE id = ? AND status = 'available';
COMMIT;
```

**Comment boxes to paste beside code**

> ① The server accepts only a future slot for today or tomorrow, between 08:00 and 22:00.
> ② The daily count must be below two before the update.
> ③ `BEGIN IMMEDIATE` and the status condition guard against double booking.

**Screenshot to take:** 学生 Study Room Booking 页，截日期切换、时间列、八个房间及红/绿/灰状态；可以再加小图截绿色格子点击后的 “Confirm booking” 弹窗。尽量用浏览器缩放使 08:00–22:00 全列可见。

**Say:** “A green cell is only a candidate. The confirmation dialog precedes the server transaction, which checks time, availability and the daily limit.”

## Slide 6 — Key SQL ③: checkout and queue allocation (2:25–2:55)

**Paste on slide**

> **Checkout updates the loan and its physical copy together**

```sql
BEGIN IMMEDIATE;
SELECT * FROM book_copies WHERE barcode = ?;
SELECT COUNT(*) FROM loans
WHERE student_id = ? AND returned_at IS NULL;
INSERT INTO loans(copy_id, student_id, borrowed_at, due_at, issued_by)
VALUES (?, ?, ?, ?, ?);
UPDATE book_copies
SET status = 'borrowed', reserved_for_student_id = NULL
WHERE id = ?;
COMMIT;
```

**Comment boxes to paste beside code**

> ① The barcode identifies one physical copy.
> ② The server checks copy status, student limit and request queue before inserting.
> ③ Returning a copy can automatically mark it reserved for the first waiting student.

**Screenshot to take:** 管理员 Circulation 的借出表单和 active loans 表，突出 student number、barcode、状态；若能截图归还后的 Requests 页面，可在右下角加一张小图表现 waiting → ready。

**Say:** “The transaction changes both the loan record and copy status. On return, the queue is checked automatically; final checkout still happens at the circulation desk.”

## Slide 7 — CRUD and database operations video (2:55–4:35)

**Paste on slide**

> **Video demo: data changes across the student and librarian views**
> Create → Read → Update → Delete, with the resulting database state visible in the UI.

**Record this exact sequence (1:40 maximum):**

1. **0:00–0:15 — Read:** Student searches a category and opens a book’s copy details.
2. **0:15–0:35 — Create:** Book a green study-room cell and confirm; show it turn red and appear in My Bookings.
3. **0:35–0:50 — Update:** Renew an eligible loan in My Loans; show the due date change. If no eligible loan remains, demonstrate a librarian edit to a book record instead.
4. **0:50–1:05 — Delete:** Cancel the created study-room booking through the API only if your UI has no cancel button; preferably use librarian Books/Copies Delete in the UI for an unreferenced test record. Do not claim an on-screen cancel action if it is absent.
5. **1:05–1:30 — Librarian:** Sign in as librarian; add a book or copy, edit it, then check a copy out or return one. Show status changes in Circulation.
6. **1:30–1:40 — Database evidence:** Show the refreshed Books/Copies/Requests list reflecting the previous action.

**Screenshot to take:** 此页放视频封面图，用管理员 Books/Copies 表格截图，并覆盖一个播放按钮。视频本身请录屏嵌入 PPT；不要用静态图冒充视频。录屏前准备好 student number、barcode 和可删除的测试记录，避免现场输入耗时。

**Say:** “The video shows the CRUD operations and how each action changes the database-backed interface.”

## Slide 8 — Reproducibility and close (4:35–5:00)

**Paste on slide**

> **Run and verify**
>
> `git clone …/COMP3278GP.git` → `cd COMP3278GP` → `python3 server.py`
> Open `http://127.0.0.1:8765/`
> SQLite is initialized on first launch with `schema.sql`, `seed.sql`, and demo records.
> `python3 -m unittest discover -s tests -v`
>
> **Takeaway:** A normalized library database with role-specific workflows and transaction-safe updates.

**Screenshot to take:** README 的 Run locally 和 Database setup and configuration 两段，裁掉无关文字；或用简洁终端截图显示启动命令和 server URL。

**Say:** “The README provides every setup step, demo accounts and database configuration. The tests use temporary databases, so the demo database is preserved.”

## Timing and group participation

| Section | Duration |
|---|---:|
| Slides 1–3: introduction, functions, ER | 1:20 |
| Slides 4–6: key SQL with matching function screenshots | 1:35 |
| Slide 7: CRUD video | 1:40 |
| Slide 8: reproducibility and closing | 0:25 |
| **Total** | **5:00** |

Assign at least one spoken segment to every actual group member. The speaker can narrate the video, but make the handoff before and after the video explicit.
