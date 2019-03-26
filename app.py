#!/usr/bin/env python

from tornado.web import RequestHandler, Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient
from tornado.template import DictLoader
from tornado import gen, options
from bs4 import BeautifulSoup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String
import re, json

options.define('port', default=5000, type=int, help='port to run on')

sqlite_engine = create_engine('sqlite:///:memory:')
Base = declarative_base()
class Alert(Base):
    __tablename__ = 'alert'
    k = Column(String, primary_key=True)
    v = Column(String)
Base.metadata.create_all(sqlite_engine)
make_session = sessionmaker(bind=sqlite_engine)

temp_loader = DictLoader({'rss.xml': '''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
 <title>{{ site }}</title>
 <link>http://wils519.herokuapp.com/{{ site }}</link>
 <description>https://github.com/wanghan519/heroku_tornado</description>
 {% for i in soup %}
 <item>
  <title>{{ i[0] }}</title>
  <link>{{ i[1] }}</link>
  <pubDate>{{ i[2] }}</pubDate>
  <description>{{ i[3] }}</description>
 </item>
 {% end %}
</channel>
</rss>
'''})

class MainHandler(RequestHandler):
    def initialize(self, make_session):
        self.db = make_session()
    def on_finish(self):
        self.db.close()
    def get(self):
        self.write(str(self.db.query(Alert).count()))

class RSSHandler(RequestHandler):
    async def get(self, site):
        if site=='tianya':
            http_client = AsyncHTTPClient()
            response = await http_client.fetch('https://bbs.tianya.cn/m/list.jsp?item=develop&order=1')
            soup = BeautifulSoup(response.body.decode('utf8'), 'html.parser')
            soup = soup.select('ul.post-list li a')
            soup = [(i.select('div.p-title')[0].get_text().strip(), 'https://bbs.tianya.cn/m/'+i.attrs['href'], i.select('span')[0].get_text(), i.select('div.author')[0].get_text().split()[0]) for i in soup[:5]]
            self.set_header('Content-Type', 'application/xml; charset=UTF-8')
            self.render('rss.xml', site=site, soup=soup)
        else:
            self.write(site)

async def stock(stock_code):
    url = 'http://hq.sinajs.cn/list=%s'%stock_code
    http_client = AsyncHTTPClient()
    response = await http_client.fetch(url)
    l1 = re.split(r'[",]', response.body.decode('cp936'))
    db = make_session()
    db.add(Alert(k=url, v=json.dumps(l1)))
    db.commit()
    l0 = db.query(Alert).filter_by(k=url).all()
    print(l0)
    db.close()

async def loop():
    while True:
        nxt = gen.sleep(60*5)
        try:
            await gen.multi(map(stock, ['sz000735', 'sh600999']))
        except Exception as e:
            print(e)
        await nxt

if __name__=='__main__':
    options.parse_command_line()
    http_server = HTTPServer(Application([
        (r'/', MainHandler, {'make_session': make_session}),
        (r'/(.*)', RSSHandler),
    ], template_loader=temp_loader))
    http_server.listen(options.options.port)
    IOLoop.current().spawn_callback(loop)
    IOLoop.current().start()
