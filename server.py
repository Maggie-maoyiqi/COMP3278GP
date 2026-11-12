import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get("DATABASE_PATH", str(ROOT / "data/library.db")))
HK_TZ = ZoneInfo("Asia/Hong_Kong")
NOW = lambda: datetime.now(HK_TZ).replace(tzinfo=None, microsecond=0)
COOKIE_SECRET = os.environ.get("LIBRARY_COOKIE_SECRET", "local-hku-library-cookie-secret").encode()


class Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class Conflict(Exception):
    pass


def connect():
    connection = sqlite3.connect(DB, factory=Connection, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def password(value, salt):
    return hashlib.pbkdf2_hmac("sha256", value.encode(), bytes.fromhex(salt), 200_000).hex()


def create_account(connection, ident, username, role, raw_password):
    salt = secrets.token_hex(16)
    connection.execute(
        "INSERT INTO accounts(id,username,password_hash,salt,role) VALUES(?,?,?,?,?)",
        (ident, username, password(raw_password, salt), salt, role),
    )


def init():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.executescript((ROOT / "schema.sql").read_text())
        ensure_book_primary_key(connection)
        if not connection.execute("SELECT 1 FROM accounts LIMIT 1").fetchone():
            create_account(connection, 1, "librarian", "admin", "Librarian123!")
            create_account(connection, 2, "student", "student", "Student123!")
            create_account(connection, 3, "student2", "student", "Student123!")
            connection.execute(
                "INSERT INTO students(id,account_id,student_no,name,email,faculty,max_loans) VALUES(1,2,'3035000001','Kayan Chan','kayan.chan@connect.hku.hk','Faculty of Engineering',5)"
            )
            connection.execute(
                "INSERT INTO students(id,account_id,student_no,name,email,faculty,max_loans) VALUES(2,3,'3035000002','Li Wenhao','manho.lee@connect.hku.hk','Faculty of Arts',5)"
            )
            connection.executescript((ROOT / "seed.sql").read_text())
        connection.execute("UPDATE students SET name='Kayan Chan' WHERE name='陈嘉欣'")
        connection.execute("UPDATE students SET name='Li Wenhao' WHERE name='李文浩'")
        ensure_identity_migration(connection)
        ensure_demo_catalog(connection)
        ensure_study_room_slots(connection)
        ensure_demo_study_room_bookings(connection)


def ensure_book_primary_key(connection):
    """Migrate the original local database from books.id to books.book_id."""
    columns = {row[1] for row in connection.execute("PRAGMA table_info(books)")}
    if "book_id" not in columns and "id" in columns:
        connection.execute("ALTER TABLE books RENAME COLUMN id TO book_id")


def ensure_identity_migration(connection):
    columns = {row[1] for row in connection.execute("PRAGMA table_info(students)")}
    if "uid" not in columns:
        connection.execute("ALTER TABLE students ADD COLUMN uid TEXT")
    if "password_hash" not in columns:
        connection.execute("ALTER TABLE students ADD COLUMN password_hash TEXT")
    if "password_salt" not in columns:
        connection.execute("ALTER TABLE students ADD COLUMN password_salt TEXT")
    connection.execute("UPDATE students SET uid=student_no WHERE uid IS NULL OR uid='' ")
    for row in connection.execute("SELECT id,uid FROM students WHERE password_hash IS NULL"):
        salt = secrets.token_hex(16)
        connection.execute("UPDATE students SET password_hash=?,password_salt=? WHERE id=?", (password("Student123!", salt), salt, row["id"]))
    connection.execute(
        "INSERT OR IGNORE INTO admins(uid,name,email,password_hash,password_salt) VALUES(?,?,?,?,?)",
        ("A001", "Library Administrator", "librarian@connect.hku.hk", password("Librarian123!", "6c6f63616c2d61646d696e2d73616c74"), "6c6f63616c2d61646d696e2d73616c74"),
    )


def ensure_demo_catalog(connection):
    """Keep the local demo catalogue rich enough to exercise search and filtering."""
    titles = [
        ("9780000000009", "Designing Data-Intensive Applications", "Computer Science"),
        ("9780000000010", "Computer Networking: A Top-Down Approach", "Computer Science"),
        ("9780000000011", "Operating System Concepts", "Computer Science"),
        ("9780000000012", "Artificial Intelligence: A Modern Approach", "Computer Science"),
        ("9780000000013", "The Pragmatic Programmer", "Computer Science"),
        ("9780000000014", "Refactoring", "Computer Science"),
        ("9780000000015", "The Art of Statistics", "Mathematics"),
        ("9780000000016", "A Brief History of Time", "Science"),
        ("9780000000017", "The Selfish Gene", "Science"),
        ("9780000000018", "Thinking, Fast and Slow", "Psychology"),
        ("9780000000019", "The Design of Everyday Things", "Design"),
        ("9780000000020", "Ways of Seeing", "Art"),
        ("9780000000021", "The Great Gatsby", "Classics"),
        ("9780000000022", "One Hundred Years of Solitude", "Classics"),
        ("9780000000023", "The Republic", "Philosophy"),
        ("9780000000024", "On Liberty", "Philosophy"),
        ("9780000000025", "The Silk Roads", "History"),
        ("9780000000026", "Hong Kong: A Cultural History", "History"),
        ("9780000000027", "Principles of Economics", "Economics"),
        ("9780000000028", "Marketing Management", "Business"),
    ]
    for index, (isbn, title, category) in enumerate(titles, 1):
        connection.execute(
            "INSERT OR IGNORE INTO books(isbn,title,subtitle,publisher,publication_year,language,category,description,cover_url) VALUES(?,?,?,?,?,?,?,?,?)",
            (isbn, title, "", "HKU Demo Press", 2020, "English", category, "Demo catalogue record for the HKU Library Portal.", ""),
        )
        book = connection.execute("SELECT book_id FROM books WHERE isbn=?", (isbn,)).fetchone()
        author_name = f"Demo Author {index}"
        connection.execute("INSERT OR IGNORE INTO authors(name) VALUES(?)", (author_name,))
        author = connection.execute("SELECT id FROM authors WHERE name=?", (author_name,)).fetchone()
        connection.execute("INSERT OR IGNORE INTO book_authors(book_id,author_id,author_order) VALUES(?,?,1)", (book["book_id"], author["id"]))
        barcode = f"HKU-DEMO-{index:04d}"
        connection.execute(
            "INSERT OR IGNORE INTO book_copies(book_id,library_id,barcode,shelf_location,status,acquired_at) VALUES(?,?,?,?,?,?)",
            (book["book_id"], 1 + (index % 3), barcode, f"Demo Shelf {index:02d}", "available", "2025-01-15"),
        )


def ensure_study_room_slots(connection):
    """Materialize eight rooms for the current and next calendar day."""
    columns = {row[1] for row in connection.execute("PRAGMA table_info(study_room_slots)")}
    if "status" not in columns:
        connection.execute("ALTER TABLE study_room_slots ADD COLUMN status TEXT NOT NULL DEFAULT 'available'")
        connection.execute("UPDATE study_room_slots SET status=CASE WHEN available=0 THEN 'booked' ELSE 'available' END")
    today = NOW().date()
    for day_offset in (0, 1):
        day = today + timedelta(days=day_offset)
        for room_no in range(1, 9):
            for hour in range(8, 22):
                slot_start = datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat()
                connection.execute(
                    "INSERT OR IGNORE INTO study_room_slots(room_no,slot_start,status) VALUES(?,?,?)",
                    (room_no, slot_start, 'available' if datetime.fromisoformat(slot_start) > NOW() else 'expired'),
                )
    connection.execute(
        "UPDATE study_room_slots SET status='expired',reserved_student_uid=NULL "
        "WHERE slot_start<=? AND status='available'",
        (NOW().isoformat(),),
    )


def ensure_demo_study_room_bookings(connection):
    """Add ten future booked cells so the student matrix has realistic demo state."""
    students = [row[0] for row in connection.execute(
        "SELECT s.student_no FROM students s JOIN accounts a ON a.id=s.account_id WHERE a.active=1 ORDER BY s.id LIMIT 2"
    ).fetchall()]
    if not students:
        return
    has_legacy_available = "available" in {row[1] for row in connection.execute("PRAGMA table_info(study_room_slots)")}
    today = NOW().date()
    candidates = []
    for day_offset in (0, 1):
        day = today + timedelta(days=day_offset)
        for hour in range(8, 22):
            start = datetime.combine(day, datetime.min.time()).replace(hour=hour).isoformat()
            if datetime.fromisoformat(start) > NOW():
                for room_no in range(1, 9):
                    candidates.append((start, room_no))
    created = 0
    for start, room_no in candidates:
        if created >= 10:
            break
        slot = connection.execute(
            "SELECT id,status FROM study_room_slots WHERE room_no=? AND slot_start=?",
            (room_no, start),
        ).fetchone()
        if not slot or slot["status"] != "available":
            continue
        if has_legacy_available:
            connection.execute(
                "UPDATE study_room_slots SET status='booked',available=0,reserved_student_uid=? WHERE id=? AND status='available'",
            (students[-1], slot["id"]),
            )
        else:
            connection.execute(
                "UPDATE study_room_slots SET status='booked',reserved_student_uid=? WHERE id=? AND status='available'",
                (students[-1], slot["id"]),
            )
        created += 1


BOOK_SELECT = """
SELECT b.*,b.book_id AS id,
       COALESCE(GROUP_CONCAT(DISTINCT a.name),'') AS authors,
       COUNT(DISTINCT bc.id) AS total_copies,
       COUNT(DISTINCT CASE WHEN bc.status='available' THEN bc.id END) AS available_copies
FROM books b
LEFT JOIN book_authors ba ON ba.book_id=b.book_id
LEFT JOIN authors a ON a.id=ba.author_id
LEFT JOIN book_copies bc ON bc.book_id=b.book_id
"""

LOAN_SELECT = """
SELECT l.*,s.student_no,s.name AS student_name,b.book_id,b.title,b.isbn,
       bc.barcode,bc.shelf_location,lib.name AS library_name
FROM loans l
JOIN students s ON s.id=l.student_id
JOIN book_copies bc ON bc.id=l.copy_id
JOIN books b ON b.book_id=bc.book_id
JOIN libraries lib ON lib.id=bc.library_id
"""

RESERVATION_SELECT = """
SELECT r.*,s.student_no,s.name AS student_name,b.title,b.isbn,
       (SELECT COUNT(*) FROM reservations ahead
        WHERE ahead.book_id=r.book_id AND ahead.status='waiting'
          AND (ahead.queued_at<r.queued_at OR (ahead.queued_at=r.queued_at AND ahead.id<=r.id))) AS queue_position
FROM reservations r
JOIN students s ON s.id=r.student_id
JOIN books b ON b.book_id=r.book_id
"""


def student_for_account(connection, account_id):
    return connection.execute("SELECT * FROM students WHERE account_id=?", (account_id,)).fetchone()


def set_book_authors(connection, book_id, names):
    clean = []
    for name in names:
        name = str(name).strip()
        if name and name not in clean:
            clean.append(name)
    if not clean:
        raise ValueError("Please provide at least one author.")
    connection.execute("DELETE FROM book_authors WHERE book_id=?", (book_id,))
    for order, name in enumerate(clean, 1):
        connection.execute("INSERT OR IGNORE INTO authors(name) VALUES(?)", (name,))
        author_id = connection.execute("SELECT id FROM authors WHERE name=?", (name,)).fetchone()["id"]
        connection.execute(
            "INSERT INTO book_authors(book_id,author_id,author_order) VALUES(?,?,?)",
            (book_id, author_id, order),
        )


def allocate_reserved_copy(connection, book_id):
    copy = connection.execute(
        "SELECT id FROM book_copies WHERE book_id=? AND status='available' ORDER BY id LIMIT 1",
        (book_id,),
    ).fetchone()
    reservation = connection.execute(
        "SELECT id,student_id FROM reservations WHERE book_id=? AND status='waiting' ORDER BY queued_at,id LIMIT 1",
        (book_id,),
    ).fetchone()
    if copy and reservation:
        connection.execute(
            "UPDATE book_copies SET status='reserved',reserved_for_student_id=? WHERE id=?",
            (reservation["student_id"], copy["id"]),
        )
        connection.execute("UPDATE reservations SET status='ready' WHERE id=?", (reservation["id"],))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "static"), **kwargs)

    def reply(self, data, status=200, cookie=None):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        size = int(self.headers.get("Content-Length", 0))
        if size > 1_000_000:
            raise ValueError("The request is too large.")
        try:
            value = json.loads(self.rfile.read(size) or b"{}")
        except json.JSONDecodeError as error:
            raise ValueError("The request body is not valid JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("The request body must be a JSON object.")
        return value

    def account(self, connection):
        token = next((part.split("=", 1)[1] for part in self.headers.get("Cookie", "").split("; ") if part.startswith("library_auth=")), None)
        if not token or "." not in token:
            return None
        payload, signature = token.rsplit(".", 1)
        expected = hmac.new(COOKIE_SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        uid, role = payload.split(":", 1)
        if role == "student":
            return connection.execute("SELECT account_id AS id,uid AS username,'student' AS role FROM students WHERE uid=?", (uid,)).fetchone()
        return connection.execute("SELECT a.id,a.username,'admin' AS role FROM admins ad JOIN accounts a ON a.role='admin' WHERE ad.uid=? AND ad.active=1 LIMIT 1", (uid,)).fetchone()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.api("GET")
        else:
            super().do_GET()

    def do_POST(self):
        self.api("POST")

    def do_PUT(self):
        self.api("PUT")

    def do_DELETE(self):
        self.api("DELETE")

    def api(self, method):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            with connect() as connection:
                account = self.account(connection)
                if path == "/api/health" and method == "GET":
                    return self.reply({"status": "ok", "database": "sqlite", "system": "HKU Library Portal"})
                if path == "/api/login" and method == "POST":
                    body = self.body()
                    email = str(body.get("email", body.get("username", ""))).strip().lower()
                    row = connection.execute("SELECT id,uid,email,password_hash,password_salt,'student' AS role FROM students WHERE lower(email)=?", (email,)).fetchone()
                    if not row:
                        row = connection.execute("SELECT uid AS id,uid,email,password_hash,password_salt,'admin' AS role FROM admins WHERE lower(email)=? AND active=1", (email,)).fetchone()
                    if not row and body.get("username"):
                        legacy = connection.execute("SELECT * FROM accounts WHERE username=? AND active=1", (body.get("username"),)).fetchone()
                        if legacy and legacy["role"] == "student":
                            row = connection.execute("SELECT id,uid,email,password_hash,password_salt,'student' AS role FROM students WHERE account_id=?", (legacy["id"],)).fetchone()
                            if row is None:
                                row = connection.execute("SELECT id,student_no AS uid,email,password_hash,? AS password_salt,'student' AS role FROM students WHERE account_id=?", (legacy["salt"], legacy["id"])).fetchone()
                        elif legacy:
                            row = {"id": "A001", "uid": "A001", "email": legacy["username"], "password_hash": legacy["password_hash"], "password_salt": legacy["salt"], "role": "admin"}
                    requested_role = body.get("role")
                    if (
                        not row
                        or requested_role not in ("student", "admin")
                        or row["role"] != requested_role
                        or not hmac.compare_digest(password(body.get("password", ""), row["password_salt"]), row["password_hash"])
                    ):
                        return self.reply({"error": "The email, password, or selected role is incorrect."}, 401)
                    payload = f"{row['uid']}:{row['role']}"
                    token = payload + "." + hmac.new(COOKIE_SECRET, payload.encode(), hashlib.sha256).hexdigest()
                    return self.reply(
                        {"username": row["email"], "role": row["role"]},
                        cookie=f"library_auth={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800",
                    )
                if not account:
                    return self.reply({"error": "Please sign in first."}, 401)
                if method != "GET":
                    origin = self.headers.get("Origin")
                    if origin and origin != f"http://{self.headers.get('Host')}":
                        return self.reply({"error": "Invalid request origin."}, 403)
                if path == "/api/me" and method == "GET":
                    data = dict(account)
                    if account["role"] == "student":
                        data["student"] = dict(student_for_account(connection, account["id"]))
                    return self.reply(data)
                if path == "/api/logout" and method == "POST":
                    return self.reply(
                        {"ok": True},
                        cookie="library_auth=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0",
                    )
                if path == "/api/demo/switch-to-student" and method == "POST":
                    if account["role"] != "admin":
                        return self.reply({"error": "Only a librarian can open the student demo account."}, 403)
                    target = connection.execute(
                        "SELECT s.uid,s.email,'student' AS role FROM students s JOIN accounts a ON a.id=s.account_id WHERE a.username='student' AND a.active=1"
                    ).fetchone()
                    if not target:
                        return self.reply({"error": "The student demo account is unavailable."}, 404)
                    payload = f"{target['uid']}:student"
                    token = payload + "." + hmac.new(COOKIE_SECRET, payload.encode(), hashlib.sha256).hexdigest()
                    return self.reply(
                        {**dict(target), "username": "student"},
                        cookie=f"library_auth={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800",
                    )
                if path == "/api/catalog" and method == "GET":
                    return self.catalog(connection, query)
                match = re.fullmatch(r"/api/books/(\d+)", path)
                if match and method == "GET":
                    return self.book_detail(connection, int(match.group(1)))
                if path.startswith("/api/student/"):
                    if account["role"] != "student":
                        return self.reply({"error": "A student account is required."}, 403)
                    return self.student_api(connection, account, path, method, query)
                if path.startswith("/api/admin/"):
                    if account["role"] != "admin":
                        return self.reply({"error": "Librarian access is required."}, 403)
                    return self.admin_api(connection, account, path, method, query)
                return self.reply({"error": "API endpoint not found."}, 404)
        except Conflict as error:
            self.reply({"error": str(error)}, 409)
        except (ValueError, KeyError, TypeError) as error:
            self.reply({"error": str(error)}, 400)
        except sqlite3.IntegrityError as error:
            self.reply({"error": "The change conflicts with a database constraint or related record.", "detail": str(error)}, 409)
        except Exception as error:
            self.log_error("API failure: %s", error)
            self.reply({"error": "The server could not process the request."}, 500)

    def catalog(self, connection, query):
        term = query.get("q", [""])[0].strip()
        category = query.get("category", [""])[0].strip()
        available = query.get("available", [""])[0] == "1"
        where, args = [], []
        if term:
            where.append("(b.title LIKE ? OR b.isbn LIKE ? OR a.name LIKE ?)")
            args.extend([f"%{term}%"] * 3)
        if category:
            where.append("b.category=?")
            args.append(category)
        sql = BOOK_SELECT
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " GROUP BY b.book_id"
        if available:
            sql += " HAVING available_copies>0"
        sql += " ORDER BY b.title"
        rows = [dict(row) for row in connection.execute(sql, args)]
        categories = [row[0] for row in connection.execute("SELECT DISTINCT category FROM books ORDER BY category")]
        return self.reply({"books": rows, "categories": categories})

    def book_detail(self, connection, book_id):
        row = connection.execute(BOOK_SELECT + " WHERE b.book_id=? GROUP BY b.book_id", (book_id,)).fetchone()
        if not row:
            return self.reply({"error": "Book record not found."}, 404)
        data = dict(row)
        data["copies"] = [
            dict(copy)
            for copy in connection.execute(
                "SELECT bc.id,bc.barcode,bc.shelf_location,bc.status,lib.name AS library_name,lib.location "
                "FROM book_copies bc JOIN libraries lib ON lib.id=bc.library_id WHERE bc.book_id=? ORDER BY lib.name,bc.barcode",
                (book_id,),
            )
        ]
        return self.reply(data)

    def student_api(self, connection, account, path, method, query=None):
        query = query or {}
        student = student_for_account(connection, account["id"])
        if path == "/api/student/overview" and method == "GET":
            counts = connection.execute(
                "SELECT COUNT(*) AS active,COALESCE(SUM(due_at<?),0) AS overdue FROM loans WHERE student_id=? AND returned_at IS NULL",
                (NOW().isoformat(), student["id"]),
            ).fetchone()
            reservations = connection.execute(
                "SELECT COUNT(*) FROM reservations WHERE student_id=? AND status IN ('waiting','ready')",
                (student["id"],),
            ).fetchone()[0]
            return self.reply({"student": dict(student), "active_loans": counts["active"], "overdue": counts["overdue"], "reservations": reservations})
        if path == "/api/student/study-room-slots" and method == "GET":
            ensure_study_room_slots(connection)
            requested_date = query.get("date", [NOW().date().isoformat()])[0]
            allowed_dates = {NOW().date().isoformat(), (NOW().date() + timedelta(days=1)).isoformat()}
            if requested_date not in allowed_dates:
                raise ValueError("Study rooms can be viewed for today or tomorrow only.")
            start = datetime.fromisoformat(requested_date).replace(hour=8).isoformat()
            end = datetime.fromisoformat(requested_date).replace(hour=22).isoformat()
            rows = connection.execute(
                "SELECT id,room_no,slot_start,status,reserved_student_uid "
                "FROM study_room_slots WHERE slot_start>=? AND slot_start<? ORDER BY slot_start,room_no",
                (start, end),
            )
            return self.reply({
                "rooms": 8,
                "hours": 14,
                "date": requested_date,
                "slots": [dict(row) for row in rows],
                "student_uid": student["student_no"],
            })
        if path == "/api/student/study-room-bookings" and method == "GET":
            rows = connection.execute(
                "SELECT id,room_no,slot_start,status,reserved_student_uid FROM study_room_slots "
                "WHERE reserved_student_uid=? AND status='booked' AND slot_start>=? ORDER BY slot_start,room_no",
                (student["student_no"], NOW().isoformat()),
            )
            return self.reply({"bookings": [dict(row) for row in rows]})
        match = re.fullmatch(r"/api/student/study-room-slots/(\d+)/reserve", path)
        if match and method == "POST":
            ensure_study_room_slots(connection)
            connection.commit()
            slot_id = int(match.group(1))
            connection.execute("BEGIN IMMEDIATE")
            slot = connection.execute(
                "SELECT * FROM study_room_slots WHERE id=? AND slot_start>=? AND slot_start<?",
                (
                    slot_id,
                    NOW().isoformat(),
                    datetime.combine(NOW().date() + timedelta(days=2), datetime.min.time()).isoformat(),
                ),
            ).fetchone()
            if not slot:
                return self.reply({"error": "This study-room slot is not available for booking."}, 404)
            if slot["status"] != "available":
                raise Conflict("This study-room slot has already been reserved.")
            day = slot["slot_start"][:10]
            daily_count = connection.execute(
                "SELECT COUNT(*) FROM study_room_slots WHERE reserved_student_uid=? AND status='booked' AND substr(slot_start,1,10)=?",
                (student["student_no"], day),
            ).fetchone()[0]
            if daily_count >= 2:
                raise Conflict("You can book at most two study-room hours per day.")
            columns = {row[1] for row in connection.execute("PRAGMA table_info(study_room_slots)")}
            if "available" in columns:
                connection.execute(
                    "UPDATE study_room_slots SET status='booked',available=0,reserved_student_uid=? WHERE id=? AND status='available'",
                    (student["student_no"], slot_id),
                )
            else:
                connection.execute(
                    "UPDATE study_room_slots SET status='booked',reserved_student_uid=? WHERE id=? AND status='available'",
                    (student["student_no"], slot_id),
                )
            return self.reply({"ok": True, "slot_id": slot_id}, 201)
        match = re.fullmatch(r"/api/student/study-room-slots/(\d+)/reserve", path)
        if match and method == "DELETE":
            slot_id = int(match.group(1))
            columns = {row[1] for row in connection.execute("PRAGMA table_info(study_room_slots)")}
            if "available" in columns:
                changed = connection.execute(
                    "UPDATE study_room_slots SET status='available',available=1,reserved_student_uid=NULL "
                    "WHERE id=? AND reserved_student_uid=? AND status='booked' AND slot_start>?",
                    (slot_id, student["student_no"], NOW().isoformat()),
                ).rowcount
            else:
                changed = connection.execute(
                    "UPDATE study_room_slots SET status='available',reserved_student_uid=NULL "
                    "WHERE id=? AND reserved_student_uid=? AND status='booked' AND slot_start>?",
                    (slot_id, student["student_no"], NOW().isoformat()),
                ).rowcount
            if not changed:
                return self.reply({"error": "Your reservation was not found."}, 404)
            return self.reply({"ok": True})
        if path == "/api/student/loans" and method == "GET":
            rows = connection.execute(
                LOAN_SELECT + " WHERE l.student_id=? ORDER BY l.returned_at IS NULL DESC,l.borrowed_at DESC",
                (student["id"],),
            )
            return self.reply([dict(row) for row in rows])
        match = re.fullmatch(r"/api/student/loans/(\d+)/renew", path)
        if match and method == "POST":
            loan = connection.execute(
                LOAN_SELECT + " WHERE l.id=? AND l.student_id=? AND l.returned_at IS NULL",
                (int(match.group(1)), student["id"]),
            ).fetchone()
            if not loan:
                return self.reply({"error": "Active loan not found."}, 404)
            if loan["renew_count"] >= 2:
                raise Conflict("This loan has reached the two-renewal limit.")
            if datetime.fromisoformat(loan["due_at"]) < NOW():
                raise Conflict("Overdue items cannot be renewed.")
            waiting = connection.execute(
                "SELECT 1 FROM reservations WHERE book_id=? AND status IN ('waiting','ready') AND student_id<>?",
                (loan["book_id"], student["id"]),
            ).fetchone()
            if waiting:
                raise Conflict("Another student has requested this book, so it cannot be renewed.")
            due = datetime.fromisoformat(loan["due_at"]) + timedelta(days=14)
            connection.execute("UPDATE loans SET due_at=?,renew_count=renew_count+1 WHERE id=?", (due.isoformat(), loan["id"]))
            return self.reply({"ok": True, "due_at": due.isoformat()})
        if path == "/api/student/reservations" and method == "GET":
            rows = connection.execute(
                RESERVATION_SELECT + " WHERE r.student_id=? ORDER BY r.queued_at DESC",
                (student["id"],),
            )
            return self.reply([dict(row) for row in rows])
        if path == "/api/student/reservations" and method == "POST":
            book_id = int(self.body().get("book_id", 0))
            if not connection.execute("SELECT 1 FROM books WHERE book_id=?", (book_id,)).fetchone():
                return self.reply({"error": "Book record not found."}, 404)
            if connection.execute("SELECT 1 FROM book_copies WHERE book_id=? AND status='available'", (book_id,)).fetchone():
                raise Conflict("A copy is currently available. Please borrow it at the service desk.")
            if connection.execute(
                "SELECT 1 FROM loans l JOIN book_copies bc ON bc.id=l.copy_id WHERE l.student_id=? AND bc.book_id=? AND l.returned_at IS NULL",
                (student["id"], book_id),
            ).fetchone():
                raise Conflict("You already have an active loan for this book.")
            cursor = connection.execute(
                "INSERT INTO reservations(student_id,book_id,queued_at) VALUES(?,?,?)",
                (student["id"], book_id, NOW().isoformat()),
            )
            return self.reply({"id": cursor.lastrowid}, 201)
        match = re.fullmatch(r"/api/student/reservations/(\d+)", path)
        if match and method == "DELETE":
            reservation = connection.execute(
                "SELECT * FROM reservations WHERE id=? AND student_id=? AND status IN ('waiting','ready')",
                (int(match.group(1)), student["id"]),
            ).fetchone()
            if not reservation:
                return self.reply({"error": "No cancellable request was found."}, 404)
            if reservation["status"] == "ready":
                connection.execute(
                    "UPDATE book_copies SET status='available',reserved_for_student_id=NULL WHERE book_id=? AND reserved_for_student_id=? AND status='reserved'",
                    (reservation["book_id"], student["id"]),
                )
            connection.execute("UPDATE reservations SET status='cancelled' WHERE id=?", (reservation["id"],))
            allocate_reserved_copy(connection, reservation["book_id"])
            return self.reply({"ok": True})
        return self.reply({"error": "API endpoint not found."}, 404)

    def admin_api(self, connection, account, path, method, query):
        if path == "/api/admin/dashboard" and method == "GET":
            row = connection.execute(
                "SELECT (SELECT COUNT(*) FROM books) books,(SELECT COUNT(*) FROM book_copies) copies,"
                "(SELECT COUNT(*) FROM loans WHERE returned_at IS NULL) active_loans,"
                "(SELECT COUNT(*) FROM loans WHERE returned_at IS NULL AND due_at<?) overdue,"
                "(SELECT COUNT(*) FROM reservations WHERE status IN ('waiting','ready')) reservations",
                (NOW().isoformat(),),
            ).fetchone()
            return self.reply(dict(row))
        if path == "/api/admin/libraries" and method == "GET":
            return self.reply([dict(row) for row in connection.execute("SELECT * FROM libraries ORDER BY name")])
        if path == "/api/admin/students" and method == "GET":
            rows = connection.execute(
                "SELECT s.*,a.username,a.active,(SELECT COUNT(*) FROM loans l WHERE l.student_id=s.id AND l.returned_at IS NULL) AS active_loans "
                "FROM students s JOIN accounts a ON a.id=s.account_id ORDER BY s.student_no"
            )
            return self.reply([dict(row) for row in rows])
        if path == "/api/admin/books" and method == "GET":
            rows = connection.execute(BOOK_SELECT + " GROUP BY b.book_id ORDER BY b.book_id DESC")
            return self.reply([dict(row) for row in rows])
        if path == "/api/admin/books" and method == "POST":
            return self.save_book(connection, None)
        match = re.fullmatch(r"/api/admin/books/(\d+)", path)
        if match and method == "PUT":
            return self.save_book(connection, int(match.group(1)))
        if match and method == "DELETE":
            if not connection.execute("DELETE FROM books WHERE book_id=?", (int(match.group(1)),)).rowcount:
                return self.reply({"error": "Book record not found."}, 404)
            return self.reply({"ok": True})
        if path == "/api/admin/copies" and method == "GET":
            rows = connection.execute(
                "SELECT bc.*,b.title,lib.name AS library_name,s.student_no AS reserved_for "
                "FROM book_copies bc JOIN books b ON b.book_id=bc.book_id JOIN libraries lib ON lib.id=bc.library_id "
                "LEFT JOIN students s ON s.id=bc.reserved_for_student_id ORDER BY bc.id DESC"
            )
            return self.reply([dict(row) for row in rows])
        if path == "/api/admin/copies" and method == "POST":
            return self.save_copy(connection, None)
        match = re.fullmatch(r"/api/admin/copies/(\d+)", path)
        if match and method == "PUT":
            return self.save_copy(connection, int(match.group(1)))
        if match and method == "DELETE":
            if not connection.execute("DELETE FROM book_copies WHERE id=?", (int(match.group(1)),)).rowcount:
                return self.reply({"error": "Copy not found."}, 404)
            return self.reply({"ok": True})
        if path == "/api/admin/loans" and method == "GET":
            active = query.get("active", [""])[0]
            sql = LOAN_SELECT
            if active == "1":
                sql += " WHERE l.returned_at IS NULL"
            sql += " ORDER BY l.returned_at IS NULL DESC,l.borrowed_at DESC"
            return self.reply([dict(row) for row in connection.execute(sql)])
        if path == "/api/admin/checkout" and method == "POST":
            return self.checkout(connection, account)
        match = re.fullmatch(r"/api/admin/loans/(\d+)/return", path)
        if match and method == "POST":
            return self.return_loan(connection, int(match.group(1)))
        if path == "/api/admin/reservations" and method == "GET":
            rows = connection.execute(RESERVATION_SELECT + " ORDER BY r.status,r.queued_at")
            return self.reply([dict(row) for row in rows])
        return self.reply({"error": "API endpoint not found."}, 404)

    def save_book(self, connection, book_id):
        body = self.body()
        required = ["isbn", "title", "publisher", "publication_year", "language", "category", "authors"]
        if any(body.get(key) in (None, "") for key in required):
            raise ValueError("ISBN, title, publisher, year, language, category, and authors are required.")
        if not re.fullmatch(r"[0-9Xx-]{10,17}", str(body["isbn"])):
            raise ValueError("The ISBN format is invalid.")
        year = int(body["publication_year"])
        values = (
            str(body["isbn"]).replace("-", ""),
            str(body["title"]).strip(),
            str(body.get("subtitle", "")).strip(),
            str(body["publisher"]).strip(),
            year,
            str(body["language"]).strip(),
            str(body["category"]).strip(),
            str(body.get("description", "")).strip(),
            str(body.get("cover_url", "")).strip(),
        )
        if book_id is None:
            cursor = connection.execute(
                "INSERT INTO books(isbn,title,subtitle,publisher,publication_year,language,category,description,cover_url) VALUES(?,?,?,?,?,?,?,?,?)",
                values,
            )
            book_id = cursor.lastrowid
            status = 201
        else:
            if not connection.execute(
                "UPDATE books SET isbn=?,title=?,subtitle=?,publisher=?,publication_year=?,language=?,category=?,description=?,cover_url=? WHERE book_id=?",
                values + (book_id,),
            ).rowcount:
                return self.reply({"error": "Book record not found."}, 404)
            status = 200
        names = body["authors"] if isinstance(body["authors"], list) else str(body["authors"]).split(",")
        set_book_authors(connection, book_id, names)
        return self.reply({"id": book_id}, status)

    def save_copy(self, connection, copy_id):
        body = self.body()
        required = ["book_id", "library_id", "barcode", "shelf_location", "status", "acquired_at"]
        if any(body.get(key) in (None, "") for key in required):
            raise ValueError("Please complete every copy field.")
        if body["status"] not in ("available", "maintenance"):
            raise ValueError("A librarian can manually set only available or maintenance.")
        try:
            datetime.strptime(body["acquired_at"], "%Y-%m-%d")
        except ValueError as error:
            raise ValueError("The acquisition date must use YYYY-MM-DD.") from error
        values = (
            int(body["book_id"]),
            int(body["library_id"]),
            str(body["barcode"]).strip(),
            str(body["shelf_location"]).strip(),
            body["status"],
            body["acquired_at"],
        )
        if copy_id is None:
            cursor = connection.execute(
                "INSERT INTO book_copies(book_id,library_id,barcode,shelf_location,status,acquired_at) VALUES(?,?,?,?,?,?)",
                values,
            )
            return self.reply({"id": cursor.lastrowid}, 201)
        current = connection.execute("SELECT status,book_id FROM book_copies WHERE id=?", (copy_id,)).fetchone()
        if not current:
            return self.reply({"error": "Copy not found."}, 404)
        if current["status"] in ("borrowed", "reserved"):
            raise Conflict("A borrowed or reserved copy cannot be edited directly.")
        if current["book_id"] != values[0] and connection.execute(
            "SELECT 1 FROM loans WHERE copy_id=? LIMIT 1", (copy_id,)
        ).fetchone():
            raise Conflict("A copy with loan history cannot be moved to another book record.")
        connection.execute(
            "UPDATE book_copies SET book_id=?,library_id=?,barcode=?,shelf_location=?,status=?,reserved_for_student_id=NULL,acquired_at=? WHERE id=?",
            values + (copy_id,),
        )
        return self.reply({"ok": True})

    def checkout(self, connection, account):
        body = self.body()
        student_no = str(body.get("student_no", "")).strip()
        barcode = str(body.get("barcode", "")).strip()
        loan_days = int(body.get("loan_days", 14))
        if not 1 <= loan_days <= 60:
            raise ValueError("The loan period must be between 1 and 60 days.")
        connection.execute("BEGIN IMMEDIATE")
        student = connection.execute(
            "SELECT s.* FROM students s JOIN accounts a ON a.id=s.account_id "
            "WHERE s.student_no=? AND a.active=1",
            (student_no,),
        ).fetchone()
        copy = connection.execute("SELECT * FROM book_copies WHERE barcode=?", (barcode,)).fetchone()
        if not student:
            raise Conflict("Student not found or the account is inactive.")
        if not copy:
            raise Conflict("Copy barcode not found.")
        if copy["status"] == "reserved" and copy["reserved_for_student_id"] != student["id"]:
            raise Conflict("This copy is reserved for another student.")
        if copy["status"] not in ("available", "reserved"):
            raise Conflict("This copy is not currently available for loan.")
        active = connection.execute(
            "SELECT COUNT(*) FROM loans WHERE student_id=? AND returned_at IS NULL", (student["id"],)
        ).fetchone()[0]
        if active >= student["max_loans"]:
            raise Conflict("This student has reached the loan limit.")
        if copy["status"] == "available":
            first_waiting = connection.execute(
                "SELECT student_id FROM reservations WHERE book_id=? AND status='waiting' ORDER BY queued_at,id LIMIT 1",
                (copy["book_id"],),
            ).fetchone()
            if first_waiting and first_waiting["student_id"] != student["id"]:
                raise Conflict("This book has a request queue. Serve the first student in line.")
        now = NOW()
        due = now + timedelta(days=loan_days)
        cursor = connection.execute(
            "INSERT INTO loans(copy_id,student_id,borrowed_at,due_at,issued_by) VALUES(?,?,?,?,?)",
            (copy["id"], student["id"], now.isoformat(), due.isoformat(), account["id"]),
        )
        connection.execute(
            "UPDATE book_copies SET status='borrowed',reserved_for_student_id=NULL WHERE id=?", (copy["id"],)
        )
        connection.execute(
            "UPDATE reservations SET status='fulfilled',fulfilled_at=? WHERE student_id=? AND book_id=? AND status IN ('waiting','ready')",
            (now.isoformat(), student["id"], copy["book_id"]),
        )
        return self.reply({"id": cursor.lastrowid, "due_at": due.isoformat()}, 201)

    def return_loan(self, connection, loan_id):
        connection.execute("BEGIN IMMEDIATE")
        loan = connection.execute(
            "SELECT l.*,bc.book_id FROM loans l JOIN book_copies bc ON bc.id=l.copy_id WHERE l.id=? AND l.returned_at IS NULL",
            (loan_id,),
        ).fetchone()
        if not loan:
            return self.reply({"error": "Active loan not found."}, 404)
        now = NOW().isoformat()
        connection.execute("UPDATE loans SET returned_at=? WHERE id=?", (now, loan_id))
        connection.execute(
            "UPDATE book_copies SET status='available',reserved_for_student_id=NULL WHERE id=?", (loan["copy_id"],)
        )
        allocate_reserved_copy(connection, loan["book_id"])
        copy = connection.execute("SELECT status,reserved_for_student_id FROM book_copies WHERE id=?", (loan["copy_id"],)).fetchone()
        return self.reply({"ok": True, "copy_status": copy["status"]})


if __name__ == "__main__":
    init()
    port = int(os.environ.get("PORT", "8000"))
    print(f"HKU Library Portal http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
