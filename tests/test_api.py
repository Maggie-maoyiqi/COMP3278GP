import http.cookiejar
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import server


class LibraryApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        server.DB = Path(cls.temp.name) / "library-test.db"
        server.init()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.http.server_port}/api/"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.temp.cleanup()

    def setUp(self):
        if server.DB.exists():
            server.DB.unlink()
        server.init()
        self.client = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def request(self, path, method="GET", body=None):
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with self.client.open(request) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def login(self, role="student"):
        username = "student" if role == "student" else "librarian"
        raw_password = "Student123!" if role == "student" else "Librarian123!"
        return self.request(
            "login", "POST", {"username": username, "password": raw_password, "role": role}
        )

    def test_authentication_and_roles(self):
        self.assertEqual(self.request("catalog")[0], 401)
        self.assertEqual(
            self.request(
                "login",
                "POST",
                {"username": "student", "password": "Student123!", "role": "admin"},
            )[0],
            401,
        )
        self.assertEqual(self.login()[0], 200)
        self.assertEqual(self.request("admin/dashboard")[0], 403)
        self.assertEqual(self.request("student/overview")[1]["student"]["student_no"], "3035000001")
        self.assertEqual(self.request("logout", "POST", {})[0], 200)
        self.assertEqual(self.request("me")[0], 401)

    def test_librarian_account_switches_to_student_demo(self):
        self.login("admin")
        status, switched = self.request("demo/switch-to-student", "POST", {})
        self.assertEqual(status, 200)
        self.assertEqual(switched["username"], "student")
        self.assertEqual(self.request("me")[1]["student"]["name"], "Kayan Chan")
        self.assertEqual(self.request("admin/dashboard")[0], 403)
        self.assertEqual(self.request("demo/switch-to-student", "POST", {})[0], 403)

    def test_student_study_room_slots_can_be_reserved_and_cancelled(self):
        self.login()
        status, rooms = self.request("student/study-room-slots")
        self.assertEqual(status, 200)
        self.assertEqual(rooms["rooms"], 8)
        self.assertEqual(rooms["hours"], 14)
        self.assertEqual(len(rooms["slots"]), 112)
        self.assertTrue(any(item["status"] == "expired" for item in rooms["slots"]))
        tomorrow = (server.NOW().date() + server.timedelta(days=1)).isoformat()
        self.assertEqual(self.request(f"student/study-room-slots?date={tomorrow}")[1]["date"], tomorrow)
        slot = next(item for item in rooms["slots"] if item["status"] == "available")
        status, result = self.request(f"student/study-room-slots/{slot['id']}/reserve", "POST", {})
        self.assertEqual(status, 201)
        current = next(item for item in self.request("student/study-room-slots")[1]["slots"] if item["id"] == slot["id"])
        self.assertEqual(current["status"], "booked")
        self.assertEqual(current["reserved_student_uid"], "3035000001")
        self.assertEqual(self.request(f"student/study-room-slots/{slot['id']}/reserve", "POST", {})[0], 409)
        self.assertEqual(self.request(f"student/study-room-slots/{slot['id']}/reserve", "DELETE", {})[0], 200)

    def test_student_study_room_daily_limit_is_two_hours(self):
        self.login()
        slots = [item for item in self.request("student/study-room-slots")[1]["slots"] if item["status"] == "available"][:3]
        self.assertEqual(self.request(f"student/study-room-slots/{slots[0]['id']}/reserve", "POST", {})[0], 201)
        self.assertEqual(self.request(f"student/study-room-slots/{slots[1]['id']}/reserve", "POST", {})[0], 201)
        self.assertEqual(self.request(f"student/study-room-slots/{slots[2]['id']}/reserve", "POST", {})[0], 409)
        self.assertEqual(len(self.request("student/study-room-bookings")[1]["bookings"]), 2)

    def test_catalog_search_filters_and_detail(self):
        self.login()
        status, result = self.request("catalog?q=database")
        self.assertEqual(status, 200)
        self.assertEqual(len(result["books"]), 2)
        fundamentals = next(
            book for book in result["books"] if book["title"] == "Fundamentals of Database Systems"
        )
        self.assertIn("Ramez Elmasri", fundamentals["authors"])
        available = self.request("catalog?category=Literature&available=1")[1]["books"]
        self.assertEqual([book["title"] for book in available], ["The Odyssey"])
        detail = self.request("books/1")[1]
        self.assertEqual(detail["total_copies"], 2)
        self.assertEqual({copy["status"] for copy in detail["copies"]}, {"available", "borrowed"})
        self.assertEqual(self.request("books/999")[0], 404)

    def test_student_reservation_and_renewal_rules(self):
        self.login()
        status, created = self.request("student/reservations", "POST", {"book_id": 6})
        self.assertEqual(status, 201)
        reservations = self.request("student/reservations")[1]
        mine = next(row for row in reservations if row["id"] == created["id"])
        self.assertEqual(mine["queue_position"], 2)
        self.assertEqual(
            self.request("student/reservations", "POST", {"book_id": 3})[0], 409
        )
        status, renewed = self.request("student/loans/1/renew", "POST", {})
        self.assertEqual(status, 200)
        self.assertEqual(renewed["due_at"][:10], "2026-11-29")
        self.assertEqual(
            self.request(f"student/reservations/{created['id']}", "DELETE")[0], 200
        )

    def test_admin_checkout_and_return_are_persistent(self):
        self.login("admin")
        status, loan = self.request(
            "admin/checkout",
            "POST",
            {"student_no": "3035000001", "barcode": "HKU-DB-0003", "loan_days": 14},
        )
        self.assertEqual(status, 201)
        with server.connect() as connection:
            copy = connection.execute(
                "SELECT status FROM book_copies WHERE barcode='HKU-DB-0003'"
            ).fetchone()
            self.assertEqual(copy["status"], "borrowed")
        status, result = self.request(f"admin/loans/{loan['id']}/return", "POST", {})
        self.assertEqual(status, 200)
        self.assertEqual(result["copy_status"], "available")
        self.assertEqual(
            self.request(f"admin/loans/{loan['id']}/return", "POST", {})[0], 404
        )

    def test_return_allocates_copy_to_first_reservation(self):
        self.login("admin")
        status, result = self.request("admin/loans/2/return", "POST", {})
        self.assertEqual(status, 200)
        self.assertEqual(result["copy_status"], "reserved")
        with server.connect() as connection:
            copy = connection.execute("SELECT * FROM book_copies WHERE id=9").fetchone()
            reservation = connection.execute(
                "SELECT * FROM reservations WHERE id=1"
            ).fetchone()
            self.assertEqual(copy["reserved_for_student_id"], 2)
            self.assertEqual(reservation["status"], "ready")
        self.assertEqual(
            self.request(
                "admin/checkout",
                "POST",
                {"student_no": "3035000001", "barcode": "HKU-LIT-0041", "loan_days": 14},
            )[0],
            409,
        )

    def test_book_and_copy_crud_with_constraints(self):
        self.login("admin")
        book_body = {
            "isbn": "9781234567890",
            "title": "Relational Design",
            "subtitle": "",
            "publisher": "HKU Press",
            "publication_year": 2026,
            "language": "English",
            "category": "Computer Science",
            "description": "Course reference.",
            "cover_url": "",
            "authors": ["Ada Author", "Ben Author"],
        }
        status, book = self.request("admin/books", "POST", book_body)
        self.assertEqual(status, 201)
        created = next(row for row in self.request("admin/books")[1] if row["id"] == book["id"])
        self.assertIn("Ada Author", created["authors"])
        copy_body = {
            "book_id": book["id"],
            "library_id": 1,
            "barcode": "HKU-TEST-0001",
            "shelf_location": "3/F TEST",
            "status": "available",
            "acquired_at": "2026-11-12",
        }
        status, copy = self.request("admin/copies", "POST", copy_body)
        self.assertEqual(status, 201)
        self.assertEqual(self.request(f"admin/books/{book['id']}", "DELETE")[0], 409)
        self.assertEqual(self.request(f"admin/copies/{copy['id']}", "DELETE")[0], 200)
        self.assertEqual(self.request(f"admin/books/{book['id']}", "DELETE")[0], 200)

    def test_database_constraints(self):
        self.login("admin")
        self.assertEqual(
            self.request(
                "admin/checkout",
                "POST",
                {"student_no": "missing", "barcode": "HKU-DB-0001", "loan_days": 14},
            )[0],
            409,
        )
        with server.connect() as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
            with self.assertRaises(Exception):
                connection.execute(
                    "INSERT INTO book_copies(book_id,library_id,barcode,shelf_location,status,reserved_for_student_id,acquired_at) "
                    "VALUES(1,1,'BROKEN','X','reserved',NULL,'2026-11-12')"
                )

    def test_inactive_student_and_copy_history_are_protected(self):
        self.login("admin")
        with server.connect() as connection:
            connection.execute("UPDATE accounts SET active=0 WHERE id=2")
        self.assertEqual(
            self.request(
                "admin/checkout",
                "POST",
                {"student_no": "3035000001", "barcode": "HKU-DB-0001", "loan_days": 14},
            )[0],
            409,
        )
        copies = self.request("admin/copies")[1]
        copy = next(item for item in copies if item["id"] == 7)
        body = {
            "book_id": 3,
            "library_id": copy["library_id"],
            "barcode": copy["barcode"],
            "shelf_location": copy["shelf_location"],
            "status": copy["status"],
            "acquired_at": copy["acquired_at"],
        }
        self.assertEqual(self.request("admin/copies/7", "PUT", body)[0], 409)


if __name__ == "__main__":
    unittest.main()
