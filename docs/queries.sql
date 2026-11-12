-- 1. 检索书目、作者及可借副本数
SELECT b.book_id,b.title,GROUP_CONCAT(a.name) AS authors,
       COUNT(DISTINCT CASE WHEN bc.status='available' THEN bc.id END) AS available_copies
FROM books b
LEFT JOIN book_authors ba ON ba.book_id=b.book_id
LEFT JOIN authors a ON a.id=ba.author_id
LEFT JOIN book_copies bc ON bc.book_id=b.book_id
WHERE b.title LIKE '%Database%' OR a.name LIKE '%Database%'
GROUP BY b.book_id;

-- 2. 学生当前借阅
SELECT s.student_no,s.name,b.title,bc.barcode,l.borrowed_at,l.due_at
FROM loans l
JOIN students s ON s.id=l.student_id
JOIN book_copies bc ON bc.id=l.copy_id
JOIN books b ON b.book_id=bc.book_id
WHERE l.returned_at IS NULL
ORDER BY l.due_at;

-- 3. 每个分类的馆藏与可借数量
SELECT b.category,COUNT(DISTINCT b.book_id) AS titles,COUNT(bc.id) AS copies,
       SUM(bc.status='available') AS available
FROM books b
LEFT JOIN book_copies bc ON bc.book_id=b.book_id
GROUP BY b.category;

-- 4. 预约队列
SELECT b.title,s.student_no,s.name,r.status,r.queued_at,
       ROW_NUMBER() OVER(PARTITION BY r.book_id ORDER BY r.queued_at,r.id) AS queue_position
FROM reservations r
JOIN books b ON b.book_id=r.book_id
JOIN students s ON s.id=r.student_id
WHERE r.status='waiting'
ORDER BY b.title,queue_position;

-- 5. 借出操作的事务示例（实际应用还会做权限和上限检查）
BEGIN IMMEDIATE;
INSERT INTO loans(copy_id,student_id,borrowed_at,due_at,issued_by)
VALUES(1,1,'2026-11-12T10:00:00','2026-11-26T10:00:00',1);
UPDATE book_copies SET status='borrowed' WHERE id=1 AND status='available';
COMMIT;
