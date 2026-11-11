import unittest,tempfile,threading,json,urllib.request,urllib.error,http.cookiejar,sqlite3
from pathlib import Path
import server
class ProjectTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();server.DB=Path(cls.tmp.name)/'test.db';server.init()
  cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler);threading.Thread(target=cls.http.serve_forever,daemon=True).start();cls.url='http://127.0.0.1:'+str(cls.http.server_port)
 @classmethod
 def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup()
 def setUp(self):self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def req(self,path,method='GET',body=None):
  req=urllib.request.Request(self.url+'/api/'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'},method=method)
  try:
   with self.client.open(req) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def login(self,role='admin'):return self.req('login','POST',{'username':role,'password':'Admin123!' if role=='admin' else 'User123!','role':role})
 def test_auth(self):
  self.assertEqual(self.req('calendar')[0],401)
  self.assertEqual(self.req('login','POST',{'username':'user','password':'User123!','role':'admin'})[0],401)
  self.assertEqual(self.login('user')[0],200);self.assertEqual(self.req('admin/runs')[0],403)
  self.assertEqual(self.req('logout','POST',{})[0],200);self.assertEqual(self.req('me')[0],401)
 def test_calendar_and_detail(self):
  self.login('user');status,rows=self.req('calendar?month=2026-06');self.assertEqual(status,200);self.assertEqual(len(rows),4)
  self.assertEqual(self.req('calendar?month=2026-06&city=%E5%8C%97%E4%BA%AC')[1],[])
  self.assertEqual(self.req('calendar?month=invalid')[0],400)
  self.assertEqual(len(self.req('runs/1')[1]['sales']),2)
  self.assertIn('温升宝',self.req('runs/1')[1]['performances'][0]['cast_text'])
  self.assertEqual(self.req('runs/999')[0],404)
 def test_crud_persistence_and_publication(self):
  self.login();b={'run_id':1,'opens_at':'2027-02-08T12:00','kind':'general','note':'test'}
  status,r=self.req('admin/sale_rounds','POST',b);self.assertEqual(status,201);ident=r['id']
  self.assertEqual(len(self.req('calendar?month=2027-02')[1]),1)
  b['note']='changed';self.assertEqual(self.req(f'admin/sale_rounds/{ident}','PUT',b)[0],200)
  with server.connect() as c:self.assertEqual(c.execute('SELECT note FROM sale_rounds WHERE id=?',(ident,)).fetchone()[0],'changed')
  self.assertEqual(self.req(f'admin/sale_rounds/{ident}','DELETE')[0],200);self.assertEqual(self.req('calendar?month=2027-02')[1],[])
  runs=self.req('admin/runs')[1];run=next(x for x in runs if x['id']==1);run.pop('id');run['published']=0
  self.req('admin/runs/1','PUT',run);self.assertEqual(len(self.req('calendar?month=2026-06')[1]),2)
  run['published']=1;self.req('admin/runs/1','PUT',run)
 def test_constraints(self):
  self.login();self.assertEqual(self.req('admin/venues','POST',{'city':'','name':'test','address':''})[0],409)
  self.assertEqual(self.req('admin/venues/1','DELETE')[0],409)
  self.assertEqual(self.req('admin/performances','POST',{'run_id':1,'starts_at':'2027-01-01T19:30','cast_text':''})[0],409)
  self.assertEqual(self.req('admin/actors')[0],404)
  self.assertEqual(self.req('admin/performances','POST',{'run_id':1,'starts_at':'bad','cast_text':''})[0],400)
  self.assertEqual(self.req('admin/accounts')[0],404)
 def test_season_distribution_and_idempotency(self):
  self.login('user')
  for month in ['2026-11','2026-12']:
   status,rows=self.req('calendar?month='+month)
   self.assertEqual(status,200);self.assertEqual(len(rows),30)
   self.assertEqual(len({r['run_id'] for r in rows}),15)
   self.assertEqual(len({r['opens_at'][:10] for r in rows}),15)
   self.assertEqual(len({r['city'] for r in rows}),5)
  with server.connect() as c:
   before=c.execute('SELECT COUNT(*) FROM performances').fetchone()[0]
   self.assertEqual(c.execute("SELECT COUNT(*) FROM performances WHERE substr(starts_at,1,7) IN ('2026-11','2026-12')").fetchone()[0],60)
  server.init()
  with server.connect() as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM performances').fetchone()[0],before)
 def test_actor_text_crud(self):
  self.login();text='演员甲、演员乙\n特别出演：演员丙 <script>'
  b={'run_id':1,'starts_at':'2026-07-09T19:30','cast_text':text}
  code,r=self.req('admin/performances','POST',b);self.assertEqual(code,201)
  detail=self.req('runs/1')[1]
  self.assertEqual(next(p for p in detail['performances'] if p['id']==r['id'])['cast_text'],text)
  b['cast_text']='新名单';self.assertEqual(self.req('admin/performances/'+str(r['id']),'PUT',b)[0],200)
  self.assertEqual(self.req('admin/performances/'+str(r['id']),'DELETE')[0],200)
 def test_upload_rejection(self):
  self.login();self.assertEqual(self.req('admin/upload','POST',{'data':'aGVsbG8='})[0],400)
if __name__=='__main__':unittest.main()
