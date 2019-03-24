#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from tornado import web, httpserver, ioloop
from tornado import gen, httpclient, template
from tornado import options
from bs4 import BeautifulSoup

options.define('port', default=5000, help='port to run on', type=int)

tl = template.DictLoader({'rss.xml': '''<?xml version="1.0" encoding="UTF-8" ?>
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

class MainHandler(web.RequestHandler):
    def get(self):
        self.write('Hello, torando.')

class RSSHandler(web.RequestHandler):
    def initialize(self, db):
        self.db = db
    @gen.coroutine
    def get(self, rss):
        if rss=='tianya':
            hc = httpclient.AsyncHTTPClient()
            response = yield hc.fetch('https://bbs.tianya.cn/m/list.jsp?item=develop&order=1')
            html = BeautifulSoup(response.body, 'html.parser')
            aa = html.select('ul.post-list li a')
            ar = [(i.select('div.p-title')[0].get_text().strip(), 'https://bbs.tianya.cn/m/'+i.attrs['href'], i.select('span')[0].get_text(), i.select('div.author')[0].get_text().split()[0]) for i in aa[:5]]
            self.set_header('Content-Type', 'application/xml; charset=UTF-8')
            self.render('rss.xml', ct=rss, ar=ar)
        else:
            self.write(rss)

if __name__=='__main__':
    options.parse_command_line()
    hs = httpserver.HTTPServer(web.Application([
        (r'/', MainHandler),
        (r'/(.*)', RSSHandler, {'db': {'id': 'text'}}),
    ], template_loader=tl))
    hs.listen(options.options.port)
    ioloop.IOLoop.current().start()
