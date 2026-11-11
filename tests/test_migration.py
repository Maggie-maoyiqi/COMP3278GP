import sqlite3, tempfile, unittest
from pathlib import Path
from migrations import migrate_text_fields
ROOT=Path(__file__).resolve().parents[1]
class MigrationTest(unittest.TestCase):
 def test_legacy_data_backup_preservation_and_repeat(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'old.db'
   with sqlite3.connect(path) as c:
    c.executescript((ROOT/'tests/fixtures/legacy-schema.sql').read_text())
    c.executescript((ROOT/'tests/fixtures/legacy-seed.sql').read_text())
    c.execute("UPDATE cities SET name='自定义上海' WHERE id=1")
    c.execute("UPDATE actors SET name='自定义演员' WHERE id=1")
   migrate_text_fields(path)
   self.assertTrue(Path(str(path)+'.before-text-v2.db').exists())
   migrate_text_fields(path)
   with sqlite3.connect(path) as c:
    c.executescript((ROOT/'schema.sql').read_text())
    self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
    self.assertEqual(c.execute('SELECT city FROM venues WHERE id=1').fetchone()[0],'自定义上海')
    self.assertIn('Eggy：自定义演员',c.execute('SELECT cast_text FROM performances WHERE id=1').fetchone()[0])
    self.assertEqual(c.execute('SELECT COUNT(*) FROM sale_rounds').fetchone()[0],4)
    self.assertFalse(c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name IN ('cities','actors','characters','casts')").fetchall())
    with self.assertRaises(sqlite3.IntegrityError):c.execute("UPDATE performances SET starts_at='2030-01-01T19:30' WHERE id=1")
