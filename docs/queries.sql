-- 在 sqlite3 data/theatre.db 中执行；CRUD 演示通过事务最终回滚，不改种子数据。
PRAGMA foreign_keys=ON;
BEGIN;
INSERT INTO sale_rounds(run_id,opens_at,kind,note) VALUES(1,'2026-11-08T12:00','general','课程 CRUD 演示');
SELECT s.id,p.title,c.name AS city,s.opens_at,s.kind FROM sale_rounds s JOIN runs r ON s.run_id=r.id JOIN productions p ON r.production_id=p.id JOIN venues v ON r.venue_id=v.id JOIN cities c ON v.city_id=c.id WHERE r.published=1 AND substr(s.opens_at,1,7)='2026-11' ORDER BY s.opens_at;
UPDATE sale_rounds SET note='修改后的说明' WHERE run_id=1 AND opens_at='2026-11-08T12:00';
SELECT substr(opens_at,1,10) AS sale_date,COUNT(*) AS round_count,COUNT(DISTINCT run_id) AS run_count FROM sale_rounds GROUP BY sale_date;
SELECT pe.starts_at,ch.name AS character,a.name AS actor FROM performances pe JOIN casts ca ON ca.performance_id=pe.id JOIN characters ch ON ch.id=ca.character_id JOIN actors a ON a.id=ca.actor_id WHERE pe.run_id=1;
DELETE FROM sale_rounds WHERE run_id=1 AND opens_at='2026-11-08T12:00';
ROLLBACK;
