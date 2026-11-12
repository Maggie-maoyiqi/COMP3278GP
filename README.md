# COMP3278 Library Portal

A relational-database course project for a university library portal. Students can search the catalogue, manage loans, join book request queues, and reserve study rooms. Librarians can manage catalogue records and physical copies, check books in and out, and review student activity.

The project uses only the Python 3.10+ standard library, native HTML/CSS/JavaScript, and SQLite. No pip or npm installation is required.

## Run locally

```sh
python3 server.py
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/) in a browser. The first run creates `data/library.db` and loads demo data.

| Role | Username | Password |
|---|---|---|
| Student | `student` | `Student123!` |
| Librarian | `librarian` | `Librarian123!` |

Stop the server with `Ctrl+C`. If port 8765 is unavailable, use:

```sh
PORT=8765 python3 server.py
```

## Features

### Student

- Search by title, author, ISBN, or category.
- View physical copies, library locations, shelves, barcodes, and statuses.
- View active and historical loans and renew eligible loans.
- Join and cancel book request queues when no copy is available.
- Book one-hour study-room slots between 08:00 and 22:00 for today or tomorrow.
- View upcoming study-room bookings; only available slots can be booked.
- Book at most two study-room hours per day, with confirmation before booking.

### Librarian

- View catalogue, copy, loan, overdue, student, and request statistics.
- Check books out using a student number and physical-copy barcode.
- Return books and automatically prepare them for the first waiting student.
- Create, edit, and delete bibliographic records and physical copies.
- Review student accounts, loans, and request queues.
- Switch to the fixed student demo account for testing.

## Database design

The schema separates bibliographic records from physical copies: `books` stores one edition, while `book_copies` stores each physical item with its own barcode and status. Loans reference physical copies; book requests reference bibliographic records.

Detailed documentation:

- [Database design](docs/database-design.md)
- [System architecture](docs/architecture.md)
- [API contract](docs/api.md)
- [ER diagram source](docs/er.mmd)
- [SQL query examples](docs/queries.sql)
- [Implementation plan](docs/planning.md)
- [Verification record](docs/verification.md)

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile server.py
node --check static/app.js
```

Tests use temporary databases and do not modify `data/library.db`.

## Project structure

```text
server.py            HTTP server, authentication, APIs, and transactions
schema.sql           Tables, foreign keys, checks, and indexes
seed.sql             Initial libraries, books, copies, loans, and requests
static/              Single-page frontend
tests/               API and database integration tests
docs/                Architecture, ER, API, and verification documents
data/library.db      Local runtime database; ignored by Git
```

## Scope

This is a local course demonstration. It does not connect to the real HKU Portal, real library data, email, payments, interlibrary loan, or RFID. A public deployment would require HTTPS, rate limiting, audit logs, backups, a production application server, and a formal identity system.
