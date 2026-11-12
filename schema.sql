PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS accounts(
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('student','admin')),
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS students(
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL UNIQUE REFERENCES accounts(id) ON DELETE CASCADE,
  student_no TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL CHECK(length(trim(name))>0),
  email TEXT NOT NULL UNIQUE,
  faculty TEXT NOT NULL DEFAULT '',
  max_loans INTEGER NOT NULL DEFAULT 5 CHECK(max_loans BETWEEN 1 AND 20)
);
CREATE TABLE IF NOT EXISTS admins(
  uid TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  password_salt TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS sessions(
  token TEXT PRIMARY KEY,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS libraries(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  location TEXT NOT NULL,
  opening_hours TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS books(
  book_id INTEGER PRIMARY KEY,
  isbn TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL CHECK(length(trim(title))>0),
  subtitle TEXT NOT NULL DEFAULT '',
  publisher TEXT NOT NULL DEFAULT '',
  publication_year INTEGER NOT NULL CHECK(publication_year BETWEEN 1000 AND 2100),
  language TEXT NOT NULL DEFAULT 'English',
  category TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  cover_url TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS authors(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE CHECK(length(trim(name))>0)
);
CREATE TABLE IF NOT EXISTS book_authors(
  book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  author_id INTEGER NOT NULL REFERENCES authors(id),
  author_order INTEGER NOT NULL DEFAULT 1 CHECK(author_order > 0),
  PRIMARY KEY(book_id,author_id)
);
CREATE TABLE IF NOT EXISTS book_copies(
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(book_id),
  library_id INTEGER NOT NULL REFERENCES libraries(id),
  barcode TEXT NOT NULL UNIQUE,
  shelf_location TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','borrowed','reserved','maintenance')),
  reserved_for_student_id INTEGER REFERENCES students(id),
  acquired_at TEXT NOT NULL,
  CHECK(status='reserved' OR reserved_for_student_id IS NULL),
  CHECK(status!='reserved' OR reserved_for_student_id IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS loans(
  id INTEGER PRIMARY KEY,
  copy_id INTEGER NOT NULL REFERENCES book_copies(id),
  student_id INTEGER NOT NULL REFERENCES students(id),
  borrowed_at TEXT NOT NULL,
  due_at TEXT NOT NULL,
  returned_at TEXT,
  renew_count INTEGER NOT NULL DEFAULT 0 CHECK(renew_count BETWEEN 0 AND 2),
  issued_by INTEGER NOT NULL REFERENCES accounts(id),
  CHECK(due_at > borrowed_at),
  CHECK(returned_at IS NULL OR returned_at >= borrowed_at)
);
CREATE TABLE IF NOT EXISTS reservations(
  id INTEGER PRIMARY KEY,
  student_id INTEGER NOT NULL REFERENCES students(id),
  book_id INTEGER NOT NULL REFERENCES books(book_id),
  status TEXT NOT NULL DEFAULT 'waiting' CHECK(status IN ('waiting','ready','fulfilled','cancelled')),
  queued_at TEXT NOT NULL,
  fulfilled_at TEXT
);

CREATE TABLE IF NOT EXISTS study_room_slots(
  id INTEGER PRIMARY KEY,
  room_no INTEGER NOT NULL CHECK(room_no BETWEEN 1 AND 8),
  slot_start TEXT NOT NULL CHECK(strftime('%H',slot_start) BETWEEN '08' AND '21'),
  status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('expired','booked','available')),
  reserved_student_uid TEXT REFERENCES students(student_no) ON DELETE SET NULL,
  UNIQUE(room_no,slot_start),
  CHECK((status='booked' AND reserved_student_uid IS NOT NULL) OR
        (status IN ('expired','available') AND reserved_student_uid IS NULL))
);

CREATE UNIQUE INDEX IF NOT EXISTS one_active_loan_per_copy ON loans(copy_id) WHERE returned_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS one_open_reservation_per_student_book ON reservations(student_id,book_id) WHERE status IN ('waiting','ready');
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_copies_book_status ON book_copies(book_id,status);
CREATE INDEX IF NOT EXISTS idx_loans_student_active ON loans(student_id,returned_at);
CREATE INDEX IF NOT EXISTS idx_reservations_queue ON reservations(book_id,status,queued_at);
CREATE INDEX IF NOT EXISTS idx_study_room_slots_time ON study_room_slots(slot_start,room_no);
CREATE INDEX IF NOT EXISTS idx_study_room_slots_student ON study_room_slots(reserved_student_uid,slot_start);
