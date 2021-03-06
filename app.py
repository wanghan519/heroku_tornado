#!/usr/bin/env python

import sys
from tornado.web import HTTPError, RequestHandler, Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient
from tornado.template import DictLoader
from bs4 import BeautifulSoup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String

SQLITE_ENGINE = create_engine('sqlite:///:memory:')
DCLR_BASE = declarative_base()
class Data(DCLR_BASE):
    __tablename__ = 'data'
    k = Column(String, primary_key=True)
    v = Column(String)
DCLR_BASE.metadata.create_all(SQLITE_ENGINE)
MAKE_SESSION = sessionmaker(bind=SQLITE_ENGINE)

TEMP_LOADER = DictLoader({'rss.xml': '''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
 <title>{{ site }}</title>
 <link>http://wils519.herokuapp.com/rss/{{ site }}</link>
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

class MyHandler(RequestHandler):
    def initialize(self):
        self.db = MAKE_SESSION()
    def on_finish(self):
        self.db.close()
    def get(self):
        self.write('test')

class RSSHandler(MyHandler):
    async def get(self, site):
        http_client = AsyncHTTPClient()
        if site=='tianya':
            response = await http_client.fetch('https://bbs.tianya.cn/m/list.jsp?item=develop&order=1')
            soup = BeautifulSoup(response.body, 'html.parser').select('ul.post-list li a')
            soup = [(i.div.get_text().strip(), 'https://bbs.tianya.cn/m/'+i['href'], i.span.string, i.find(class_='author').get_text().split()[0]) for i in soup[:5]]
        elif site=='uzb':
            response = await http_client.fetch('http://www.uzaobao.com/plus/list.php?tid=28')
            soup = BeautifulSoup(response.body, 'html.parser').select('div.listbox ul.e2 li')
            soup = [(i.find(class_='title').string, 'http://www.uzaobao.com'+i.find(class_='title')['href'], i.find(class_='info').contents[2], i.find(class_='intro').string) for i in soup[:5]]
        else:
            raise HTTPError(404)
        self.set_header('Content-Type', 'application/xml; charset=UTF-8')
        self.render('rss.xml', site=site, soup=soup)

class HTMLHandler(RequestHandler):
    async def get(self, site):
        http_client = AsyncHTTPClient()
        response = await http_client.fetch(site)
        self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.write(response.body)

if __name__=='__main__':
    http_server = HTTPServer(Application([
        (r'/', MyHandler),
        (r'/rss/(.+)', RSSHandler),
        (r'/(http.+)', HTMLHandler),
    ], template_loader=TEMP_LOADER, static_path='./'))
    http_server.listen(sys.argv[1] if len(sys.argv)==2 else 5000)
    IOLoop.current().start()
