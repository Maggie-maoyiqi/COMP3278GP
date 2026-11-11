# 幕间 · 开票日历

根据提供的小程序截图实现的课程全栈项目：日历、城市筛选、开票详情、排期/票版图、角色登录及管理员数据库 CRUD。Python 3.10+ 标准库、原生 HTML/CSS/JavaScript、SQLite；无需 pip/npm install。

## 从源码启动

### 环境要求

- Git（也可以在 GitHub 点击 **Code → Download ZIP**，解压后进入项目目录）
- Python **3.10 或更高版本**，启用标准库 SQLite（官方 Python 安装包通常已包含）
- 现代浏览器，例如 Chrome、Edge 或 Safari
- 无需安装 Node.js、npm 包或 pip 包；Node.js 仅用于可选的 JavaScript 语法检查

### 1. 下载源码

```sh
git clone https://github.com/Maggie-maoyiqi/COMP3278GP.git
cd COMP3278GP
```

### 2. 检查环境并启动

macOS / Linux：

```sh
python3 --version
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
python3 server.py
```

Windows（PowerShell / 命令提示符）：

```powershell
py -3 --version
py -3 -c "import sqlite3; print(sqlite3.sqlite_version)"
py -3 server.py
```

若电脑没有 `py` 命令，可以使用 `python`，但请确认版本至少为 3.10。

### 3. 打开网站

保持终端运行，在浏览器打开 **http://127.0.0.1:8000/**。前端页面和后端 API 由同一个 Python 服务提供，不需要分别启动。请通过上述地址访问，不要直接双击 `static/index.html`。停止服务时在终端按 `Ctrl+C`。

首次启动自动创建 `data/theatre.db`、SQL 表和演示数据。数据库文件不随源码上传，每位同学启动时会自动生成自己的本地数据库；以后启动保留修改。SQLite 是实际持久化 SQL 数据库，无需另装数据库服务器。若课程指定 MySQL，需另做方言迁移，当前脚本不能直接当作 MySQL DDL。

### 4. 登录体验

| 身份 | 账号 | 密码 |
|---|---|---|
| 用户 | user | User123! |
| 管理员 | admin | Admin123! |

选择匹配身份后登录。管理员登录后点击“信息管理”。可按“城市 → 场馆 → 剧目 → 演出批次 → 开票轮次 → 轮次渠道”录入；排期可按“演员 → 剧中角色 → 演出场次 → 场次卡司”录入。表单用下拉框选取外键，图片可上传也可填 URL；演出批次切换为“已发布”，用户即可在该轮次的开票日期看到信息。管理表显示数据库 ID，便于课程展示。

默认展示 2026-11-11。新增 11/12 月各 15 个模拟批次，每月 30 场演出、30 个开票轮次，覆盖上海、北京、广州、杭州、深圳；共 30 批次、60 场次、60 轮次。开票日分布在每月 1、3、5…29 日，演出在同月举行。所有新增节目明确标注为课程模拟数据，并沿用演示海报；不为虚构批次附上原截图的真实排期图。原 6 月参考记录保留作历史示例。

点击日历上方漏斗“筛选”按钮，滑动城市列表，可多选；点击“完成”应用，清空选择后完成恢复全部城市；关闭/Escape/点击外部不应用未确认的选择。日期选择与月份导航保持不变。

启动时通过 data_migrations 版本记录增量导入模拟数据，保留已有修改，不会重复生成。更新源码后请重启服务并刷新浏览器，以应用代码与增量演示数据。

## 设计资料
- `docs/database-design.md`：草稿修正、实体属性、基数、候选键、3NF、约束与课堂符号对应
- `docs/er.mmd`：含属性的 Crow's Foot ER 图 Mermaid 源码
- `docs/er.svg`：可直接打开的 ER 图
- `schema.sql`：实际运行的 SQL 建表、索引、触发器
- `seed.sql`：业务种子数据
- `docs/api.md`：API 合约及错误格式
- `docs/queries.sql`：INSERT/UPDATE/DELETE/JOIN/GROUP BY 演示
- `docs/planning.md`、`docs/verification.md`：实施和验收记录

## 验证
```sh
python3 -m unittest discover -s tests -v
node --check static/app.js
```
测试使用临时数据库，不会修改演示库。默认账号仅用于本地教学。生产部署需要 HTTPS、登录限速、账号管理和备份等措施，当前仅监听本机。

## 常见问题与配置

**端口 8000 已被占用**：改用 8765，并打开 http://127.0.0.1:8765/。

macOS / Linux：

```sh
PORT=8765 python3 server.py
```

Windows PowerShell：

```powershell
$env:PORT="8765"
py -3 server.py
```

Windows 命令提示符（CMD）：

```bat
set PORT=8765
py -3 server.py
```

**需要独立测试数据库**：启动前设置 `DATABASE_PATH`，例如 macOS/Linux 使用 `DATABASE_PATH=data/my-demo.db python3 server.py`；PowerShell 使用 `$env:DATABASE_PATH="data/my-demo.db"` 后启动。相对路径以运行命令时的目录为基准。不要把自己的数据库文件或登录会话提交到 Git。

**想恢复初始数据**：先停止服务并备份 `data/theatre.db`，再把该文件重命名为 `theatre.backup.db`，然后重新启动。服务会创建新的演示库，旧修改仍保留在备份文件中。

**登录提示身份不匹配**：账号、密码和下拉框的用户/管理员角色必须对应。

**看不到演出**：默认选中 2026 年 11 月 11 日，也可切换到 12 月；点击有绿色标记的日期。检查城市筛选，清空后点“完成”可显示全部城市。管理员新增批次须设为“已发布”并添加开票轮次。

**页面无法打开**：确认终端仍在运行、浏览器端口与 `PORT` 一致。服务仅监听本机 `127.0.0.1`，这套命令用于本地源码演示。

## 目录结构

```text
server.py          Python HTTP 服务、API、登录和数据库 CRUD
demo_data.py       11/12 月增量模拟数据（只导入一次）
schema.sql         建表、索引和跨表约束
seed.sql           原截图参考数据
static/            页面、CSS、JavaScript 与演示图片
docs/              ER 图、设计说明、API 与 SQL 示例
tests/             使用临时数据库的 API 集成测试
data/              启动时生成的数据库（不提交）
```

Windows 运行自动化测试时可将上文的 `python3` 换成 `py -3`。测试不要求先启动服务，会在临时端口运行测试服务并自动结束。
