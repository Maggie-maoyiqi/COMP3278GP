import os, json, sqlite3, secrets, hashlib, hmac, base64, re
from demo_data import seed_season
from pathlib import Path
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT=Path(__file__).resolve().parent
DB=Path(os.environ.get('DATABASE_PATH',str(ROOT/'data/theatre.db')))
TABLES={
 'cities':['name'], 'venues':['city_id','name','address'],
 'productions':['title','description','poster_url'],
 'runs':['production_id','venue_id','start_date','end_date','schedule_url','seatmap_url','published'],
 'performances':['run_id','starts_at'], 'actors':['name'],
 'characters':['production_id','name'], 'casts':['performance_id','character_id','actor_id'],
 'sale_rounds':['run_id','opens_at','kind','note'], 'channels':['name','url'],
 'sale_channels':['sale_round_id','channel_id','eligibility']}
class Connection(sqlite3.Connection):
 def __exit__(self,*args):
  try: return super().__exit__(*args)
  finally: self.close()

def connect():
 c=sqlite3.connect(DB,factory=Connection); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c

def password(p,s): return hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(s),200000).hex()
def init():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with connect() as c:
  c.executescript((ROOT/'schema.sql').read_text())
  if not c.execute('SELECT 1 FROM accounts LIMIT 1').fetchone():
   for username,role,pw in [('admin','admin','Admin123!'),('user','user','User123!')]:
    salt=secrets.token_hex(16); c.execute('INSERT INTO accounts(username,password_hash,salt,role) VALUES(?,?,?,?)',(username,password(pw,salt),salt,role))
   c.executescript((ROOT/'seed.sql').read_text())
  seed_season(c)

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT/'static'),**kw)
 def reply(self,data,status=200,cookie=None):
  raw=json.dumps(data,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers(); self.wfile.write(raw)
 def body(self):
  n=int(self.headers.get('Content-Length',0))
  if n>6_000_000: raise ValueError('请求内容过大')
  return json.loads(self.rfile.read(n) or b'{}')
 def account(self,c):
  token=next((v.split('=',1)[1] for v in self.headers.get('Cookie','').split('; ') if v.startswith('session=')),None)
  return c.execute('SELECT a.id,a.username,a.role FROM sessions s JOIN accounts a ON a.id=s.account_id WHERE s.token=? AND s.expires_at > ?', (token,datetime.now(timezone.utc).isoformat())).fetchone()
 def do_GET(self):
  if self.path.startswith('/api/'): self.api('GET')
  else: super().do_GET()
 def do_POST(self): self.api('POST')
 def do_PUT(self): self.api('PUT')
 def do_DELETE(self): self.api('DELETE')
 def api(self,method):
  try:
   path=urlparse(self.path).path; q=parse_qs(urlparse(self.path).query)
   with connect() as c:
    user=self.account(c)
    if path=='/api/health': return self.reply({'status':'ok','database':'sqlite'})
    if path=='/api/login' and method=='POST':
     b=self.body(); a=c.execute('SELECT * FROM accounts WHERE username=?',(b.get('username'),)).fetchone()
     if not a or not hmac.compare_digest(password(b.get('password',''),a['salt']),a['password_hash']) or a['role']!=b.get('role'):return self.reply({'error':'账号、密码或角色不匹配'},401)
     token=secrets.token_urlsafe(32); c.execute('INSERT INTO sessions VALUES(?,?,?)',(token,a['id'],(datetime.now(timezone.utc)+timedelta(hours=8)).isoformat()))
     return self.reply({'username':a['username'],'role':a['role']},cookie=f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800')
    if not user:return self.reply({'error':'请先登录'},401)
    if method!='GET':
     origin=self.headers.get('Origin')
     if origin and origin!=f'http://{self.headers.get("Host")}':return self.reply({'error':'无效来源'},403)
    if path=='/api/me':return self.reply(dict(user))
    if path=='/api/logout' and method=='POST':
     c.execute('DELETE FROM sessions WHERE account_id=?',(user['id'],));return self.reply({'ok':True},cookie='session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
    if path=='/api/cities' and method=='GET':return self.reply([dict(r) for r in c.execute('SELECT * FROM cities ORDER BY id')])
    if path=='/api/calendar' and method=='GET':
     month=q.get('month',['2026-06'])[0]
     if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])',month):raise ValueError('月份格式应为 YYYY-MM')
     cities=q.get('city',[]); args=[month]; where=''
     if cities:where=' AND v.city_id IN ('+','.join('?' for _ in cities)+')';args+=cities
     rows=c.execute('''SELECT s.*,p.title,p.poster_url,r.start_date,r.end_date,v.name venue,ci.name city,ci.id city_id FROM sale_rounds s JOIN runs r ON r.id=s.run_id JOIN productions p ON p.id=r.production_id JOIN venues v ON v.id=r.venue_id JOIN cities ci ON ci.id=v.city_id WHERE r.published=1 AND substr(s.opens_at,1,7)=?'''+where+' ORDER BY s.opens_at,s.id',args)
     return self.reply([dict(r) for r in rows])
    if re.fullmatch(r'/api/runs/\d+',path) and method=='GET':
     rid=int(path.split('/')[-1]); r=c.execute('''SELECT r.*,p.title,p.description,p.poster_url,v.name venue,ci.name city FROM runs r JOIN productions p ON p.id=r.production_id JOIN venues v ON v.id=r.venue_id JOIN cities ci ON ci.id=v.city_id WHERE r.id=? AND (r.published=1 OR ?='admin')''',(rid,user['role'])).fetchone()
     if not r:return self.reply({'error':'演出不存在'},404)
     d=dict(r);d['sales']=[dict(x) for x in c.execute('SELECT * FROM sale_rounds WHERE run_id=? ORDER BY opens_at',(rid,))]
     for s in d['sales']:s['channels']=[dict(x) for x in c.execute('SELECT ch.*,sc.eligibility FROM channels ch JOIN sale_channels sc ON ch.id=sc.channel_id WHERE sc.sale_round_id=?',(s['id'],))]
     d['performances']=[dict(x) for x in c.execute('SELECT * FROM performances WHERE run_id=? ORDER BY starts_at',(rid,))]
     for p in d['performances']:p['cast']=[dict(x) for x in c.execute('SELECT a.name actor,ch.name character FROM casts ca JOIN actors a ON a.id=ca.actor_id JOIN characters ch ON ch.id=ca.character_id WHERE ca.performance_id=?',(p['id'],))]
     return self.reply(d)
    if path.startswith('/api/admin/'):
     if user['role']!='admin':return self.reply({'error':'需要管理员权限'},403)
     if path=='/api/admin/upload' and method=='POST':
      b=self.body();raw=base64.b64decode(b['data'],validate=True)
      ext='png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else 'jpg' if raw.startswith(b'\xff\xd8\xff') else None
      if not ext or len(raw)>4_000_000:raise ValueError('仅支持 4MB 内 PNG/JPEG 图片')
      folder=ROOT/'static/uploads';folder.mkdir(exist_ok=True);name=secrets.token_hex(16)+'.'+ext;(folder/name).write_bytes(raw);return self.reply({'url':'/uploads/'+name},201)
     parts=path.split('/');table=parts[3];ident=parts[4] if len(parts)>4 else None
     if table not in TABLES or (ident and not ident.isdigit()):return self.reply({'error':'资源不存在'},404)
     if method=='GET':return self.reply([dict(x) for x in c.execute(f'SELECT * FROM {table} ORDER BY id DESC')])
     if method=='DELETE' and ident:
      if not c.execute(f'DELETE FROM {table} WHERE id=?',(ident,)).rowcount:return self.reply({'error':'记录不存在'},404)
      return self.reply({'ok':True})
     if method in ('POST','PUT'):
      b=self.body();fields=TABLES[table]
      if set(b)!=set(fields):raise ValueError('请填写所有字段，且不要添加未知字段')
      for key,value in b.items():
       if key.endswith('_url') and value and not (str(value).startswith('/uploads/') or re.match(r'^https?://',str(value))):raise ValueError('图片/渠道地址须为 http(s) URL 或上传路径')
       if key in ('start_date','end_date'):
        if datetime.strptime(value,'%Y-%m-%d').strftime('%Y-%m-%d')!=value:raise ValueError('日期格式错误')
       if key in ('opens_at','starts_at'):
        if datetime.strptime(value,'%Y-%m-%dT%H:%M').strftime('%Y-%m-%dT%H:%M')!=value:raise ValueError('日期时间格式错误')
      if method=='POST':
       cur=c.execute(f'INSERT INTO {table} ({",".join(fields)}) VALUES ({",".join("?" for _ in fields)})',[b[k] for k in fields]);return self.reply({'id':cur.lastrowid},201)
      if not ident:raise ValueError('缺少记录 ID')
      if not c.execute(f'UPDATE {table} SET '+','.join(f'{k}=?' for k in fields)+' WHERE id=?',[b[k] for k in fields]+[ident]).rowcount:return self.reply({'error':'记录不存在'},404)
      return self.reply({'ok':True})
    return self.reply({'error':'接口不存在'},404)
  except (ValueError,KeyError,TypeError) as e:self.reply({'error':str(e)},400)
  except sqlite3.IntegrityError as e:self.reply({'error':'违反数据库约束（重复记录、日期范围或关联记录）。请先处理引用数据。','detail':str(e)},409)
  except Exception as e:
   self.log_error('API failure: %s',e);self.reply({'error':'服务器处理失败'},500)
if __name__=='__main__':
 init();port=int(os.environ.get('PORT','8000'));print(f'开票日历 http://127.0.0.1:{port}',flush=True);ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
