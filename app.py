#!/usr/bin/env python2
from tornado import web, httpserver, ioloop
from tornado import gen, httpclient, template
from tornado import options
from bs4 import BeautifulSoup

options.define('port', default=5000, help='port to run on', type=int)

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
            self.write(self.tl.generate(ct=rss, ar=ar))
        else:
            self.write(rss)

class App(web.Application):
    def __init__(self):
        handlers = [
            (r'/', MainHandler),
            (r'/(.*)', RSSHandler),
        ]
        settings = {}
        super(App, self).__init__(handlers, **settings)
        self.tl = template.Template('''<?xml version="1.0" encoding="UTF-8" ?>
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

if __name__=='__main__':
    options.parse_command_line()
    hs = httpserver.HTTPServer(App())
    hs.listen(options.options.port)
    ioloop.IOLoop.instance().start()
