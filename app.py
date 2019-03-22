#!/usr/bin/env python2
from tornado import web, httpserver, ioloop
from tornado import gen, httpclient, template
from bs4 import BeautifulSoup
import os

tl = template.Template('''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
 <title>{{ ct }}</title>
 <link>http://wils519.herokuapp.com/{{ ct }}</link>
 <description>https://github.com/wanghan519/heroku_tornado</description>
 {% for i in ar %}
 <item>
  <title>{{ escape(i[0]) }}</title>
  <link>{{ escape(i[1]) }}</link>
  <pubDate>{{ escape(i[2]) }}</pubDate>
  <description>{{ escape(i[3]) }}</description>
 </item>
 {% end %}
</channel>
</rss>
''')

class MainHandler(web.RequestHandler):
    def get(self):
        self.write('Hello, torando.')

class RSSHandler(web.RequestHandler):
    @gen.coroutine
    def get(self, rss):
        if rss=='tianya':
            hc = httpclient.AsyncHTTPClient()
            response = yield hc.fetch('https://bbs.tianya.cn/m/list.jsp?item=develop&order=1')
            html = BeautifulSoup(response.body, 'html.parser')
            aa = html.select('ul.post-list li a')
            ar = [(i.select('div.p-title')[0].get_text().strip(), 'https://bbs.tianya.cn/m/'+i.attrs['href'], i.select('span')[0].get_text(), i.select('div.author')[0].get_text().split()[0]) for i in aa[:5]]
            self.set_header('Content-Type', 'text/xml; charset=UTF-8')
            self.write(tl.generate(ct=rss, ar=ar))
        else:
            self.write(rss)

if __name__=='__main__':
    application = web.Application([
            (r'/', MainHandler),
            (r'/(.*)', RSSHandler),
        ])
    hs = httpserver.HTTPServer(application)
    hs.listen(int(os.environ.get('PORT', 5000)))
    ioloop.IOLoop.instance().start()
