INSERT INTO venues VALUES(1,'上海','星空间28号 · 好好有戏小剧场','上海市（演示地址）'),(2,'上海','十二楼音乐之城一号【小说编辑部】','上海市（演示地址）');
INSERT INTO productions VALUES(1,'#0528','一扇门后，一场关于相遇的故事。截图参考信息，供课程演示。','/uploads/0528.jpg'),(2,'小说','THE FICTION · 音乐剧。截图参考信息，供课程演示。','/uploads/fiction.jpg');
INSERT INTO runs VALUES(1,1,1,'2026-07-08','2026-08-02','/uploads/schedule-0528.jpg','/uploads/seat-0528.jpg',1),(2,2,2,'2026-06-23','2026-07-31','/uploads/schedule-fiction.jpg','/uploads/seat-fiction.jpg',1);
INSERT INTO sale_rounds VALUES(1,1,'2026-06-10T12:00','priority','好好有戏公众号 / 大麦优先购'),(2,1,'2026-06-10T12:30','general','全网开票'),(3,2,'2026-06-10T19:00','priority','淘麦 VIP 专享购'),(4,2,'2026-06-10T19:30','general','全网开票');
INSERT INTO channels VALUES(1,'大麦',''),(2,'好好有戏公众号',''),(3,'猫眼',''),(4,'十二楼票务中心','');
INSERT INTO sale_channels VALUES(1,1,1,'优先购资格'),(2,1,2,'公众号渠道'),(3,2,1,''),(4,3,1,'淘麦 VIP'),(5,3,4,'会员'),(6,4,1,''),(7,4,3,'');
INSERT INTO performances VALUES(1,1,'2026-07-08T19:30','Eggy：温升宝；Brandon：林大钦；Doris：刘瀚聪'),(2,2,'2026-06-23T19:30','格雷·亨特：许昌泰；怀特·希斯曼：万钰彬；休·戴克：林志明');
