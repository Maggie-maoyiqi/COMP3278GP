# 业务分析与数据库设计

## 草稿修正
草稿中能辨认出剧目、poster、日期、时间、location、演员、角色、座位、manager、用户，以及“2026上海/杭州”一类节点。部分连线没有明确基数，因此以下是基于页面重新建模的结果，而非认定草稿每条线的原意。

1. “2026上海”是一个演出批次的实例，不是实体类型。抽象为 Run，用外键关联剧目与场馆；城市由场馆确定，避免在批次重复存储 city。
2. 日期/时间是属性，开票时间属于 SaleRound，演出时间属于 Performance；两者独立，6 月 10 日开票不意味着当天演出。
3. 剧目 Production 是作品，Run 是该作品在某个场馆的一段演出安排，Performance 是其中具体一次演出。同剧可巡演、多批次，不应把场馆和城市直接固定在剧目上。
4. 演员不是角色的单值属性，同一角色可以由不同演员在不同场次扮演。Cast 是场次、角色、演员的关联实体，UNIQUE(performance_id, character_id) 表示一场一个角色只有一个演员；如需双卡司同场需调整业务规则。
5. poster、排期图、票版图均以图片地址属性存储。结构化卡司仍须独立入库，不能只存一张排期图片。
6. 截图只有座位区域/价格示意，无选座或购票功能，因此不凭空建立订单、座位库存。票版图属于批次展示资源；未来选座应增加 Seat/PriceTier/Inventory/Order。
7. 管理员与用户使用同一个 Account 实体，role 为互斥角色。当前只实现维护权限，不把“管理员负责上传”错误解释成每份信息只能由某一管理员拥有。若需审计可增 created_by 和审计表。
8. 城市过滤选择、日历某天开票数量属于查询参数/派生值，不是需要持久化的实体或计数字段。

## 关系（最小/最大基数）
城市 1 — 0..N 场馆；每个场馆恰属于一个城市。
剧目 1 — 0..N 批次；场馆 1 — 0..N 批次；每个批次必须关联一个剧目和一个场馆。
批次 1 — 0..N 场次、1 — 0..N 开票轮次（草稿允许尚未录入场次/开票）。
剧目 1 — 0..N 角色。场次、角色、演员分别 1 — 0..N 卡司记录，卡司记录各必有一个引用。
开票轮次 M — N 售票渠道，经 SaleChannel 分解；资格要求属于该关联而非渠道本身。
账户 1 — 0..N 登录会话。浏览行为不构成必须保存的用户与剧目关系。

## 实体与属性（数据字典）
所有业务表 id 均为 INTEGER PRIMARY KEY（代理键），其余类型见下表。除注明可空外均 NOT NULL；当前空图片/链接/说明以空字符串表示，无多值字段。日期采用 ISO 字符串，API 验证格式，时间统一 UTC+8 的本地业务时间；会话到期时间为 UTC。

| 实体 / 表 | 属性（除 id） | 键与规则 |
|---|---|---|
| Account / accounts | username TEXT, password_hash TEXT, salt TEXT, role TEXT | username UNIQUE；role user/admin；密码 PBKDF2 哈希 |
| Session / sessions | token TEXT PK（无 id）, account_id INTEGER FK, expires_at TEXT | 删除账户级联会话 |
| City / cities | name TEXT | 名称 UNIQUE、非空白 |
| Venue / venues | city_id INTEGER FK, name TEXT, address TEXT | UNIQUE(city_id,name) |
| Production / productions | title TEXT, description TEXT, poster_url TEXT | 标题非空白；作品名不假定全球唯一 |
| Run / runs | production_id INTEGER FK, venue_id INTEGER FK, start_date TEXT, end_date TEXT, schedule_url TEXT, seatmap_url TEXT, published INTEGER | end>=start；published 0/1 |
| Performance / performances | run_id INTEGER FK, starts_at TEXT | UNIQUE(run_id,starts_at)；必须在批次日期范围内 |
| Actor / actors | name TEXT | 姓名不设 UNIQUE，允许同名演员 |
| Character / characters | production_id INTEGER FK, name TEXT | UNIQUE(production_id,name) |
| Cast / casts | performance_id INTEGER FK, character_id INTEGER FK, actor_id INTEGER FK | UNIQUE(performance_id,character_id)；角色须属于该场剧目 |
| SaleRound / sale_rounds | run_id INTEGER FK, opens_at TEXT, kind TEXT, note TEXT | kind priority/general；UNIQUE(run_id,opens_at,kind) |
| Channel / channels | name TEXT, url TEXT | name UNIQUE |
| SaleChannel / sale_channels | sale_round_id INTEGER FK, channel_id INTEGER FK, eligibility TEXT | UNIQUE(sale_round_id,channel_id) |

## 规范化与约束
1NF：各列单值；开票渠道和演员都通过关联表记录，不把斜杠拼接字符串作为关系的唯一数据来源（note 是展示文案）。2NF：代理主键单列；候选复合键的非键属性依赖完整关系，例如渠道资格依赖轮次与渠道组合。3NF：城市名称只在 cities、场馆信息只在 venues、剧目信息只在 productions；批次不重复保存 city_name/production_title。

各表 id → 其余属性。业务候选键包括城市名、城市+场馆名、剧目+角色名、批次+场次时间、场次+角色、轮次+渠道等。ER 图只表达外键基数，跨表“角色属于同剧”和时间包含关系由触发器补充，并覆盖更新操作。

删除策略：引用中的城市、场馆、剧目、演员、角色、渠道受 FK RESTRICT 保护。删除批次会级联删除其场次、卡司、开票轮次和渠道关联；删除轮次删除渠道关联，保留渠道本身。事务失败自动回滚。草稿/发布是批次属性，用户无法读取未发布内容。

截图显示 8 场开票但只提供两部剧完整信息。本项目只录入能辨认的 2 个批次、4 个轮次，没有虚构其余 6 场；初始日历特意选中 2026-06-10 便于演示。海报/排期/票版图从所给截图裁取，原图文字清晰度受截图限制。结构化场次仅各录入一条，管理员可继续补全。

## 与课堂符号的对应
本项目提供 Crow's Foot 逻辑 ER 图。若课堂要求 Chen：每个实体画矩形、属性画椭圆、主键下划线、关系画菱形，标注上述 1:N/M:N 和参与性；Cast 可作为三元关系映射为表，SaleChannel 是带 eligibility 属性的 M:N 关系。尚未收到课件，不能声称完全符合某位老师的专用画法。当前设计按标准关系建模与 3NF 实现。
