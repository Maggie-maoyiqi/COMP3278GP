import sqlite3
import unittest
from pathlib import Path


class SchemaTest(unittest.TestCase):
    def test_schema_can_be_applied_twice(self):
        schema = (Path(__file__).resolve().parents[1] / "schema.sql").read_text()
        with sqlite3.connect(":memory:") as connection:
            connection.executescript(schema)
            connection.executescript(schema)
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            self.assertTrue(
                {"books", "book_copies", "loans", "reservations", "students"}.issubset(tables)
            )


if __name__ == "__main__":
    unittest.main()
