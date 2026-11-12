INSERT INTO libraries VALUES
 (1,'Main Library','Main Building, The University of Hong Kong','Mon–Sun 08:30–22:00'),
 (2,'Chi Wah Learning Commons','Centennial Campus','Mon–Sun 07:30–23:00'),
 (3,'Yu Chun Keung Medical Library','21 Sassoon Road','Mon–Fri 08:30–21:00');

INSERT INTO books VALUES
 (1,'9780133970777','Fundamentals of Database Systems','Seventh Edition','Pearson',2016,'English','Computer Science','A comprehensive introduction to database design, SQL, transactions and distributed databases.',''),
 (2,'9780073523323','Database System Concepts','Seventh Edition','McGraw-Hill',2019,'English','Computer Science','Core concepts in relational databases, storage, query processing and transaction management.',''),
 (3,'9780262033848','Introduction to Algorithms','Third Edition','MIT Press',2009,'English','Computer Science','A rigorous introduction to algorithms and data structures.',''),
 (4,'9780131103627','The C Programming Language','Second Edition','Prentice Hall',1988,'English','Computer Science','The classic reference for the C programming language.',''),
 (5,'9780140449136','The Odyssey','','Penguin Classics',2003,'English','Literature','Homer’s epic poem in a modern English translation.',''),
 (6,'9780199535569','Pride and Prejudice','','Oxford University Press',2008,'English','Literature','Jane Austen’s novel of manners, family and self-knowledge.',''),
 (7,'9789622090460','A Modern History of Hong Kong','','Hong Kong University Press',2007,'English','History','A political and social history of Hong Kong.',''),
 (8,'9780132350884','Clean Code','A Handbook of Agile Software Craftsmanship','Prentice Hall',2008,'English','Computer Science','Practical guidance for writing readable and maintainable software.','');

INSERT INTO authors VALUES
 (1,'Ramez Elmasri'),(2,'Shamkant B. Navathe'),(3,'Abraham Silberschatz'),(4,'Henry F. Korth'),
 (5,'S. Sudarshan'),(6,'Thomas H. Cormen'),(7,'Brian W. Kernighan'),(8,'Dennis M. Ritchie'),
 (9,'Homer'),(10,'Jane Austen'),(11,'Steve Tsang'),(12,'Robert C. Martin');

INSERT INTO book_authors VALUES
 (1,1,1),(1,2,2),(2,3,1),(2,4,2),(2,5,3),(3,6,1),(4,7,1),(4,8,2),
 (5,9,1),(6,10,1),(7,11,1),(8,12,1);

INSERT INTO book_copies VALUES
 (1,1,1,'HKU-DB-0001','3/F QA76.9.D3','available',NULL,'2024-08-20'),
 (2,1,1,'HKU-DB-0002','3/F QA76.9.D3','borrowed',NULL,'2024-08-20'),
 (3,2,1,'HKU-DB-0003','3/F QA76.9.D3','available',NULL,'2024-08-20'),
 (4,2,2,'HKU-DB-0004','Level 2 QA76.9.D3','maintenance',NULL,'2024-08-20'),
 (5,3,1,'HKU-CS-0011','3/F QA76.6','available',NULL,'2023-09-01'),
 (6,3,2,'HKU-CS-0012','Level 2 QA76.6','available',NULL,'2023-09-01'),
 (7,4,1,'HKU-CS-0021','3/F QA76.73.C15','available',NULL,'2022-01-10'),
 (8,5,1,'HKU-LIT-0031','4/F PA4025','available',NULL,'2021-06-18'),
 (9,6,1,'HKU-LIT-0041','4/F PR4034','borrowed',NULL,'2021-06-18'),
 (10,7,1,'HKU-HIS-0051','2/F DS796.H7','available',NULL,'2020-03-11'),
 (11,8,1,'HKU-CS-0061','3/F QA76.76.D47','available',NULL,'2024-01-15');

INSERT INTO loans VALUES
 (1,2,1,'2026-11-01T10:00:00','2026-11-15T23:59:59',NULL,0,1),
 (2,9,2,'2026-10-15T14:30:00','2026-10-29T23:59:59',NULL,0,1),
 (3,7,1,'2026-09-01T11:00:00','2026-09-15T23:59:59','2026-09-13T16:20:00',1,1);

INSERT INTO reservations VALUES
 (1,2,6,'waiting','2026-11-10T09:20:00',NULL);
