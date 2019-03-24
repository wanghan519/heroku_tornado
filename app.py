#!/usr/bin/env python

from tornado.web import RequestHandler, Application
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient
from tornado.template import DictLoader
from tornado import gen, options
from bs4 import BeautifulSoup

options.define('port', default=5000, help='port to run on', type=int)

tl = DictLoader({'rss.xml': '''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
 <title>{{ ct }}</title>
 <link>http://wils519.herokuapp.com/{{ ct }}</link>
 <description>https://github.com/wanghan519/heroku_tornado</description>
 {% for i in ar %}
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
    def get(self):
        self.write('Hello, torando.')

class RSSHandler(RequestHandler):
    def initialize(self, db):
        self.db = db
    async def get(self, rss):
        if rss=='tianya':
            hc = AsyncHTTPClient()
            response = await hc.fetch('https://bbs.tianya.cn/m/list.jsp?item=develop&order=1')
            html = BeautifulSoup(response.body, 'html.parser')
            aa = html.select('ul.post-list li a')
            ar = [(i.select('div.p-title')[0].get_text().strip(), 'https://bbs.tianya.cn/m/'+i.attrs['href'], i.select('span')[0].get_text(), i.select('div.author')[0].get_text().split()[0]) for i in aa[:5]]
            self.set_header('Content-Type', 'application/xml; charset=UTF-8')
            self.render('rss.xml', ct=rss, ar=ar)
        else:
            self.write(rss)

async def lp():
    while True:
        gs = gen.sleep(60*5)
        print('asdf')
        await gs

if __name__=='__main__':
    options.parse_command_line()
    hs = HTTPServer(Application([
        (r'/', MainHandler),
        (r'/(.*)', RSSHandler, {'db': {'id': 'text'}}),
    ], template_loader=tl))
    hs.listen(options.options.port)
    IOLoop.current().spawn_callback(lp)
    IOLoop.current().start()
