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
import re

options.define('port', default=5000, type=int, help='port to run on')

engn = create_engine('sqlite:///:memory:')
Base = declarative_base()
class Alert(Base):
    __tablename__ = 'alert'
    k = Column(String, primary_key=True)
    v = Column(String)
    t = Column(String)
Base.metadata.create_all(engn)
sssm = sessionmaker(bind=engn)

tmpl = DictLoader({'rss.xml': '''<?xml version="1.0" encoding="UTF-8" ?>
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
    def initialize(self, sssm):
        self.db = sssm()
    def on_finish(self):
        self.db.close()
    def get(self):
        self.write(self.db.query(Alert).first().v)

class RSSHandler(RequestHandler):
    async def get(self, site):
        if site=='tianya':
            ashc = AsyncHTTPClient()
            rspn = await ashc.fetch('https://bbs.tianya.cn/m/list.jsp?item=develop&order=1')
            soup = BeautifulSoup(rspn.body.decode('utf8'), 'html.parser')
            soup = soup.select('ul.post-list li a')
            soup = [(i.select('div.p-title')[0].get_text().strip(), 'https://bbs.tianya.cn/m/'+i.attrs['href'], i.select('span')[0].get_text(), i.select('div.author')[0].get_text().split()[0]) for i in soup[:5]]
            self.set_header('Content-Type', 'application/xml; charset=UTF-8')
            self.render('rss.xml', site=site, soup=soup)
        else:
            self.write(site)

async def loop():
    while True:
        gens = gen.sleep(60*5)
        db = sssm()
        ashc = AsyncHTTPClient()
        rspn = await ashc.fetch('http://hq.sinajs.cn/list=%s'%'sz000735')
        lst1 = re.split(r'[",]', rspn.body.decode('cp936'))
        db.add(Alert(k=lst1[1], v=lst1[4], t='stock'))
        db.commit()
        db.close()
        await gens

if __name__=='__main__':
    options.parse_command_line()
    htts = HTTPServer(Application([
        (r'/', MainHandler, {'sssm': sssm}),
        (r'/(.*)', RSSHandler),
    ], template_loader=tmpl))
    htts.listen(options.options.port)
    IOLoop.current().spawn_callback(loop)
    IOLoop.current().start()
