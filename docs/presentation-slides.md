# COMP3278 Library Portal - Presentation Slide Plan

This plan follows the assessment structure: submission reproducibility (30 marks) is supported by the README, while the five-minute presentation addresses functionality/design, ER design, SQL, CRUD/database video demonstration, and group participation.

## Presentation constraints

- Total presentation time: 5 minutes.
- Embedded video demonstration: no more than 2 minutes.
- Every group member speaks.
- Keep the slide deck visual: use the ER diagram, one architecture diagram, and a small number of screenshots rather than dense paragraphs.

## Slide 1 - Project overview (0:00-0:25)

**Title:** COMP3278 Library Portal

**Put on the slide:**

- A web-based university library system.
- Student portal + librarian portal.
- SQLite relational database with a Python standard-library backend.
- One sentence on the problem: manage bibliographic records, physical copies, loans, requests, and study-room slots in one consistent system.

**Speaker notes:** Introduce the project, group members, and the two user roles. State that the presentation will show both the database design and a short working demonstration.

## Slide 2 - User functions and interface design (0:25-0:55)

**Title:** What users can do

**Put on the slide:**

| Student | Librarian |
|---|---|
| Search by title, author, ISBN, category | Manage books and physical copies |
| View loans and renew eligible loans | Check books out and process returns |
| Join/cancel book request queues | View students, loans, overdue items, and queues |
| Reserve 08:00-22:00 study-room slots | Switch to student demo view for testing |

Add two small screenshots: catalogue search and study-room booking matrix.

**Speaker notes:** Explain that the sidebar separates My Loans, Study Room Booking, My Bookings, and My Requests. Only available room slots can be booked; the UI asks for confirmation and the server enforces the daily limit of two hours.

## Slide 3 - System architecture and security boundary (0:55-1:20)

**Title:** Application architecture

**Put on the slide:**

```text
Browser (HTML/CSS/JS)
        |
        | JSON HTTP API + HttpOnly signed cookie
        v
Python standard-library HTTP server
        |
        | role checks, transactions, validation
        v
SQLite database
  schema.sql + seed.sql + demo migrations
```

- Student and librarian routes are checked server-side.
- Passwords are stored as salted PBKDF2-HMAC hashes.
- SQLite foreign keys, CHECK constraints, unique indexes, and write transactions protect consistency.

**Speaker notes:** Emphasize that the browser is not trusted for permissions or booking limits; the backend repeats all important checks.

## Slide 4 - ER diagram and normalization (1:20-2:00)

**Title:** ER design: bibliographic records versus physical copies

**Put on the slide:** Use the ER diagram from `docs/er.mmd` or `docs/er.svg`.

Highlight these relationships:

- `BOOK 1:N BOOK_COPY`: one edition can have many physical copies.
- `BOOK M:N AUTHOR`: normalized through `BOOK_AUTHOR`.
- `STUDENT 1:N LOAN`: loan history belongs to a student and a physical copy.
- `BOOK 1:N RESERVATION`: requests form a queue for a bibliographic record.
- `STUDY_ROOM 1:N ROOM_SLOT`: each room has hourly slots; a slot can be booked at most once.

**Speaker notes:** Explain that `books.book_id` is the primary key and `isbn` is a unique business identifier. A loan points to `book_copies`, while a request points to `books`; this prevents duplicated title and copy data and supports multiple copies of one edition.

## Slide 5 - Important integrity constraints (2:00-2:25)

**Title:** Database rules that protect correctness

**Put on the slide:**

- `UNIQUE(isbn)` and `UNIQUE(barcode)` prevent duplicate identifiers.
- Partial unique index: one active loan per physical copy.
- Partial unique index: one open request per student and book.
- Study-room slot unique key: one room and hour has one row.
- `status` checks prevent invalid book-copy and room-slot states.
- Foreign keys prevent orphan copies, loans, requests, and bookings.

**Speaker notes:** Connect each rule to a user-visible behavior: no double checkout, no duplicate request, and no double booking.

## Slide 6 - Key SQL transaction: librarian checkout (2:25-2:55)

**Title:** A transaction is more than one SQL statement

**Put on the slide:** Show a shortened, commented SQL sequence:

```sql
BEGIN IMMEDIATE;
-- Lock the write transaction.
SELECT * FROM book_copies WHERE barcode = ?;
-- Check the student's active-loan count.
SELECT COUNT(*) FROM loans
WHERE student_id = ? AND returned_at IS NULL;
-- Insert the loan and update the physical copy together.
INSERT INTO loans(copy_id, student_id, borrowed_at, due_at, issued_by)
VALUES (?, ?, ?, ?, ?);
UPDATE book_copies SET status = 'borrowed' WHERE id = ?;
COMMIT;
```

**Speaker notes:** Explain that `BEGIN IMMEDIATE` prevents two librarians from passing the same availability check simultaneously. The transaction either records both changes or none.

## Slide 7 - Two-minute video demonstration (2:55-4:45)

**Title:** Live workflow: student to librarian

**Video storyboard (maximum 110 seconds):**

1. **0:00-0:15** - Student signs in and searches by category; show the filtered result count.
2. **0:15-0:35** - Open Study Room Booking; switch Today/Tomorrow; point out expired, booked, and available cells.
3. **0:35-0:55** - Click an available slot; show the confirmation dialog; confirm booking; show My Bookings.
4. **0:55-1:15** - Open My Loans; show an active loan and a renewal action.
5. **1:15-1:35** - Sign out from My Account and sign in as librarian.
6. **1:35-1:50** - Show dashboard, book/copy records, and circulation checkout/return.
7. **1:50-2:00** - Show the request queue and explain automatic ready-state allocation after return.

**Speaker notes:** Keep the video focused on CRUD and database operations required by the rubric. Use prepared demo data so no typing or waiting is needed.

## Slide 8 - Reproducibility and conclusion (4:45-5:00)

**Title:** Reproducible submission

**Put on the slide:**

- Clone `COMP3278GP`, `cd COMP3278GP`, run `python3 server.py`.
- The backend serves the frontend at `http://127.0.0.1:8765/`.
- Startup creates SQLite data, applies `schema.sql`, and loads `seed.sql` plus demo records.
- Verification: `python3 -m unittest discover -s tests -v`.
- Final takeaway: normalized data model + transaction-safe operations + two role-specific workflows.

**Speaker notes:** Close by reminding the audience that the README contains installation, database setup, configuration, demo accounts, and verification commands. Thank the audience and invite questions.

## Suggested speaker allocation

| Member | Slides | Focus |
|---|---|---|
| Member 1 | 1-2 | Problem, users, and interface |
| Member 2 | 3-4 | Architecture and ER diagram |
| Member 3 | 5-6 | Constraints and SQL transactions |
| Member 4 | 7-8 | Video demonstration, reproducibility, conclusion |

Adjust the allocation to the actual group size, but ensure every member has a speaking segment.
