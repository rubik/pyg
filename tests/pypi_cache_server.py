#!/usr/bin/env python
# Copy of http://sharebear.co.uk/blog/2009/09/17/very-simple-python-caching-proxy/

REAL_SERVER = "http://pypi.python.org"
PROXY_PORT = 8080

import BaseHTTPServer
import hashlib
import os
import cgi
import urllib2

class CacheHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            postvars = {}
        return self.do_GET(''.join(''.join(x) for x in postvars.iteritems()))

    def do_GET(self, args=''):
        print '-'*80
        m = hashlib.md5()
        m.update(self.path)
        m.update(args)
        cache_filename = m.hexdigest()
        if os.path.exists(cache_filename):
            print "Cache hit"
            data = open(cache_filename).readlines()
        else:
            print "Cache miss", self.path
            data = urllib2.urlopen(REAL_SERVER + self.path).readlines()
            open(cache_filename, 'wb').writelines(data)
        self.send_response(200)
        self.end_headers()
        self.wfile.writelines(data)
        print "-eot-"

    do_POST = do_GET

def run():
    server_address = ('0.0.0.0', PROXY_PORT)
    httpd = BaseHTTPServer.HTTPServer(server_address, CacheHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    run()
