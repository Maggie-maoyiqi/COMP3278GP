# ER 图与数据库设计（文本演员名单版，待审）

本版按项目需求简化：不建立城市、演员、剧中角色和卡司关联表。城市是场馆的文本属性；完整演员名单是具体演出场次的文本属性。ER 图见 [er.svg](er.svg)，可编辑源码见 [er.mmd](er.mmd)。

## 为什么仍区分剧目、批次和场次
以《小说》为例：Production 表示作品；Run 表示该作品在某个场馆从开始日期到结束日期的一批演出；Performance 表示其中某天 19:30 的一次演出。不同日期可以使用不同演员，所以 cast_text 放在 Performance，而非把所有日期的名单固定到 Run。SaleRound 则表示开票：6 月 10 日售票和 6 月 23 日演出是两个时间概念。

城市 city 放在 Venue，因为场馆决定其城市。Run 通过 venue_id 查询即可获得城市，不再重复存 city，也没有 City 表。漏斗城市列表来自 SELECT DISTINCT city FROM venues，添加新城市只需填写场馆，无需先维护城市实体。

## 实体与属性

| 表 | 属性 | 约束 |
|---|---|---|
| productions 剧目 | id INTEGER PK、title TEXT、description TEXT、poster_url TEXT | 标题非空白 |
| venues 场馆 | id INTEGER PK、city TEXT、name TEXT、address TEXT | 城市/名称非空白；UNIQUE(city,name) |
| runs 演出批次 | id INTEGER PK、production_id INTEGER FK、venue_id INTEGER FK、start_date TEXT、end_date TEXT、schedule_url TEXT、seatmap_url TEXT、published INTEGER | end_date≥start_date；published 为 0/1 |
| performances 演出场次 | id INTEGER PK、run_id INTEGER FK、starts_at TEXT、cast_text TEXT | UNIQUE(run_id,starts_at)；时间必须在所属批次范围内 |
| sale_rounds 开票轮次 | id INTEGER PK、run_id INTEGER FK、opens_at TEXT、kind TEXT、note TEXT | kind 为 priority/general；UNIQUE(run_id,opens_at,kind) |
| channels 售票渠道 | id INTEGER PK、name TEXT、url TEXT | 渠道名 UNIQUE |
| sale_channels 轮次渠道 | id INTEGER PK、sale_round_id INTEGER FK、channel_id INTEGER FK、eligibility TEXT | UNIQUE(sale_round_id,channel_id) |
| accounts 账户 | id INTEGER PK、username TEXT、password_hash TEXT、salt TEXT、role TEXT | 用户名 UNIQUE；role 为 user/admin；不存明文密码 |
| sessions 登录会话 | token TEXT PK、account_id INTEGER FK、expires_at TEXT | 到期后不能访问 API |

所有列 NOT NULL。可选文案/图片用空字符串。日期为 YYYY-MM-DD，业务日期时间为 YYYY-MM-DDTHH:mm（UTC+8），会话到期采用 UTC。data_migrations 是导入版本记录的技术表，不是业务实体，因此不在 ER 图中；字段为 version TEXT PK。

## 关系与基数

- Production 1 — 0..N Run：每个批次必须属于一部剧目，剧目可以尚无批次。
- Venue 1 — 0..N Run：每个批次必须指定一个场馆，场馆可承接多个批次。
- Run 1 — 0..N Performance：每场演出恰属一个批次，草稿批次允许尚未添加场次。
- Run 1 — 0..N SaleRound：一个批次可先后优先开票、普通开票或加场开票。
- SaleRound 1 — 0..N SaleChannel，Channel 1 — 0..N SaleChannel：将轮次与渠道的 M:N 关系拆为关联表。eligibility（会员等条件）依赖该组合。
- Account 1 — 0..N Session：同一个账号可有多个登录会话，角色字段决定权限，不另设管理员实体。

不存在用户到演出的保存关系，因为当前只浏览，没有收藏或订单。管理员维护信息是一项权限，不意味着某批次只能属于某管理员。截图中的座位只是票版图，不涉及库存或订单表。

## 演员名单文本示例与取舍

```text
Eggy：温升宝
Brandon：林大钦
Doris：刘瀚聪
```

数据库只保存一个 cast_text 字符串；角色名可以写入文案，也可只填写“演员甲、演员乙、演员丙”。系统不解析、不拆表，详情原样安全转义显示。空名单显示“待公布”。

这一设计满足“整份名单以文本维护”的展示需求，减少录入步骤，但不能保证演员姓名一致、角色覆盖完整，也不能通过演员外键关联其他资料。若把名单当成多个可独立查询的演员值，它不符合课堂严格原子化多值属性的建模意图；不能因为 SQL 类型是 TEXT 就宣称解决了 1NF。因此本版对演员名单有明确的非结构化文案取舍，不能宣称整个演员数据模型严格满足 3NF。其余关系避免把剧目/场馆信息复制到批次，使用主外键和完整组合候选键。

## 删除与跨表约束

剧目、场馆和渠道存在引用时禁止删除。删除批次级联删除场次和开票轮次，删除轮次级联删除渠道关联，保留渠道本身。删除账户级联删除会话。触发器约束演出日期，并禁止把批次日期缩短到排除已有场次。SQL 失败会回滚事务。

## 旧数据库迁移

启动时检测旧 cities 表，自动创建 theatre.db.before-text-v2.db 备份。迁移将旧城市名复制到 venues.city，按卡司 ID 顺序把角色名与演员名合并为 performances.cast_text，保留业务 ID、时间、图片、开票关联和账号数据，删除四张旧表。迁移在事务内执行，失败回滚；成功后不重复执行。已有同名备份且仍是旧表结构时中止，避免覆盖备份。

新安装直接用 schema.sql 创建新版表，不依赖旧迁移。迁移后要重启旧服务，否则旧进程的 SQL 会引用已经移除的表。

## 课堂图形对应

提供的是 Crow's Foot 逻辑 ER 图，含 PK/FK 和最小/最大基数。若课堂指定 Chen 符号：实体改矩形、属性改椭圆、主键下划线、关系改菱形，基数沿用。city 与 cast_text 是属性椭圆，不画成独立实体；整份名单按当前产品约定视为非结构化文案。尚未获得课件，不能代替老师对规范化要求的确认。
