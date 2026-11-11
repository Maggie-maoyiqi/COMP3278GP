"""Versioned, additive classroom fixtures. Never overwrite existing records."""
from datetime import date, timedelta

def seed_season(c):
 c.execute('CREATE TABLE IF NOT EXISTS data_migrations(version TEXT PRIMARY KEY)')
 if c.execute('SELECT 1 FROM data_migrations WHERE version=?',('season-2026-v1',)).fetchone():return
 cities=['上海','北京','广州','杭州','深圳']
 channel=c.execute('SELECT id FROM channels ORDER BY id LIMIT 1').fetchone()[0]
 for m in [11,12]:
  for i in range(15):
   city=cities[i%5];title=['夜航来信','冬日序曲','月光车站','第十二封信','星河之间'][i%5]
   venue=c.execute('INSERT INTO venues(city,name,address) VALUES(?,?,?)',(city,f'幕间演示剧场 {m}-{i+1:02d}','课程模拟场馆，非真实地址')).lastrowid
   production=c.execute('INSERT INTO productions(title,description,poster_url) VALUES(?,?,?)',(f'{title} · {m}月第{i+1:02d}期','课程模拟演出，仅用于测试日历与数据库功能，不代表真实票务信息。','/uploads/'+('0528.jpg' if i%2==0 else 'fiction.jpg'))).lastrowid
   sale_day=date(2026,m,1)+timedelta(days=i*2)
   first=min(sale_day+timedelta(days=3),date(2026,m,28))
   last=first+timedelta(days=1)
   run=c.execute('INSERT INTO runs(production_id,venue_id,start_date,end_date,schedule_url,seatmap_url,published) VALUES(?,?,?,?,?,?,1)',(production,venue,first.isoformat(),last.isoformat(),'','')).lastrowid
   for day in [first,last]:c.execute('INSERT INTO performances(run_id,starts_at,cast_text) VALUES(?,?,?)',(run,day.isoformat()+'T19:30','模拟演员甲、模拟演员乙、模拟演员丙'))
   for kind,time in [('priority','12:00'),('general','19:30')]:
    sale=c.execute('INSERT INTO sale_rounds(run_id,opens_at,kind,note) VALUES(?,?,?,?)',(run,sale_day.isoformat()+'T'+time,kind,'课程模拟开票 · 非真实票务')).lastrowid
    c.execute('INSERT INTO sale_channels(sale_round_id,channel_id,eligibility) VALUES(?,?,?)',(sale,channel,'模拟会员资格' if kind=='priority' else ''))
 c.execute('INSERT INTO data_migrations VALUES(?)',('season-2026-v1',))
