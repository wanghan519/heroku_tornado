#!/usr/bin/env python

from tornado.web import RequestHandler, Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient
from tornado.template import DictLoader
from tornado import options
from bs4 import BeautifulSoup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String
import time

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

class MainHandler(RequestHandler):
    def initialize(self, make_session):
        self.db = make_session()
    def on_finish(self):
        self.db.close()
    def get(self):
        self.write('test')

class RSSHandler(RequestHandler):
    async def get(self, site):
        if site=='tianya':
            http_client = AsyncHTTPClient()
            response = await http_client.fetch('https://bbs.tianya.cn/m/list.jsp?item=develop&order=1')
            soup = BeautifulSoup(response.body, 'html.parser').select('ul.post-list li a')
            soup = [(i.div.get_text().strip(), 'https://bbs.tianya.cn/m/'+i['href'], i.span.string, i.find(class_='author').get_text().split()[0]) for i in soup[:5]]
            self.set_header('Content-Type', 'application/xml; charset=UTF-8')
            self.render('rss.xml', site=site, soup=soup)
        elif site=='nytimes':
            http_client = AsyncHTTPClient()
            response = await http_client.fetch('https://www.nytimes.com/section/business/economy')
            soup = BeautifulSoup(response.body, 'html.parser').select('ol li.css-ye6x8s')
            soup = [(i.h2.string, 'https://www.nytimes.com'+i.a['href'], i.a['href'][1:11], i.p.string) for i in soup[:5]]
            self.set_header('Content-Type', 'application/xml; charset=UTF-8')
            self.render('rss.xml', site=site, soup=soup)
        elif site.startswith('bqk'):
            http_client = AsyncHTTPClient()
            response = await http_client.fetch('https://www.biqukan.com/%s/'%site[3:])
            soup = BeautifulSoup(response.body, 'html.parser').select('div.listmain dl dd a')
            soup = [(i.string, 'https://www.biqukan.com'+i['href'], str(time.time()), i.string) for i in soup[:5]]
            self.set_header('Content-Type', 'application/xml; charset=UTF-8')
            self.render('rss.xml', site=site, soup=soup)
        else:
            self.write(site)

if __name__=='__main__':
    options.parse_command_line()
    http_server = HTTPServer(Application([
        (r'/', MainHandler, {'make_session': make_session}),
        (r'/rss/(.*)', RSSHandler),
    ], template_loader=temp_loader, static_path='./'))
    http_server.listen(options.options.port)
    IOLoop.current().start()
