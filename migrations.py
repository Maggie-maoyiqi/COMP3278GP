"""Upgrade legacy city/cast tables without losing user data."""
import sqlite3
from pathlib import Path

def migrate_text_fields(path):
 if not path.exists():return
 c=sqlite3.connect(path)
 try:
  if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='cities'").fetchone():return
  backup=Path(str(path)+'.before-text-v2.db')
  if backup.exists():raise RuntimeError(f'迁移备份已存在，请先检查旧迁移状态：{backup}')
  with sqlite3.connect(backup) as dest:c.backup(dest)
  c.execute('PRAGMA foreign_keys=OFF')
  c.execute('BEGIN IMMEDIATE')
  try:
   for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
    c.execute('DROP TRIGGER "'+name.replace('"','""')+'"')
   c.execute("CREATE TABLE venues_new(id INTEGER PRIMARY KEY,city TEXT NOT NULL CHECK(length(trim(city))>0),name TEXT NOT NULL CHECK(length(trim(name))>0),address TEXT NOT NULL,UNIQUE(city,name))")
   c.execute('INSERT INTO venues_new SELECT v.id,ci.name,v.name,v.address FROM venues v JOIN cities ci ON ci.id=v.city_id')
   c.execute("CREATE TABLE performances_new(id INTEGER PRIMARY KEY,run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,starts_at TEXT NOT NULL,cast_text TEXT NOT NULL DEFAULT '',UNIQUE(run_id,starts_at))")
   c.execute('INSERT INTO performances_new(id,run_id,starts_at) SELECT id,run_id,starts_at FROM performances')
   for (pid,) in c.execute('SELECT id FROM performances').fetchall():
    rows=c.execute('SELECT ch.name,a.name FROM casts ca JOIN characters ch ON ch.id=ca.character_id JOIN actors a ON a.id=ca.actor_id WHERE ca.performance_id=? ORDER BY ca.id',(pid,)).fetchall()
    c.execute('UPDATE performances_new SET cast_text=? WHERE id=?',('\n'.join(f'{role}：{actor}' for role,actor in rows),pid))
   for table in ['casts','characters','actors','performances','venues','cities']:c.execute(f'DROP TABLE {table}')
   c.execute('ALTER TABLE venues_new RENAME TO venues')
   c.execute('ALTER TABLE performances_new RENAME TO performances')
   if c.execute('PRAGMA foreign_key_check').fetchall():raise RuntimeError('迁移外键检查失败')
   c.commit()
  except Exception:
   c.rollback();raise
 finally:c.close()
