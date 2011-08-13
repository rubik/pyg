'''
Pypi cache server
Original author: Victor-mortal
'''

import os
import httplib
import urlparse
import logging
import locale
import json
import hashlib
import webob
import gevent
from gevent import wsgi as wsgi_fast, pywsgi as wsgi, monkey

CACHE_DIR = '.cache'
wsgi = wsgi_fast # comment to use pywsgi

host = '0.0.0.0'
port = 8080


class Proxy(object):
    """A WSGI based web proxy application
    """

    def __init__(self, chunkSize=4096, timeout=60, dropHeaders=['transfer-encoding'], pypiHost=None, log=None):
        """
        @param log: logger of logging library
        """
        self.log = log
        if self.log is None:
            self.log = logging.getLogger('proxy')

        self.chunkSize = chunkSize
        self.timeout = timeout
        self.dropHeaders = dropHeaders
        self.pypiHost = pypiHost

    def yieldData(self, response, cache_file=None):
        while True:
            data = response.read(self.chunkSize)
            yield data
            if cache_file:
                cache_file.write(data)
            if len(data) < self.chunkSize:
                break
        if cache_file:
            cache_file.close()

    def _rewrite(self, req, start_response):
        path = req.path_info
        if req.query_string:
            path += '?' + req.query_string
        parts = urlparse.urlparse(path)
        headers = req.headers

        md = hashlib.md5()
        md.update(' '.join('%s:%s'%v for v in headers.iteritems()))
        md.update(path)

        cache_file = os.path.join(CACHE_DIR, md.hexdigest())
        if os.path.exists(cache_file):
            o = json.load( open(cache_file+'.js', 'rb') )
            start_response(o['response'], o['headers'])
            return self.yieldData( open(cache_file) )

        self.log.debug('Request from %s to %s', req.remote_addr, path)

        url = path
        conn = httplib.HTTPConnection(self.pypiHost, timeout=self.timeout)
        #headers['X-Forwarded-For'] = req.remote_addr
        #headers['X-Real-IP'] = req.remote_addr

        try:
            conn.request(req.method, url, headers=headers, body=req.body)
            response = conn.getresponse()
        except Exception, e:
            msg = str(e)
            if os.name == 'nt':
                _, encoding = locale.getdefaultlocale()
                msg = msg.decode(encoding)
            self.log.warn('Bad gateway with reason: %s', msg, exc_info=True)
            start_response('502 Bad gateway', [])
            return ['Bad gateway']

        headers = [(k, v) for (k, v) in response.getheaders()\
                   if k not in self.dropHeaders]
        start_response('%s %s' % (response.status, response.reason),
                       headers)
        json.dump( {'headers': headers, 'response': '%s %s' % (response.status, response.reason)}, open(cache_file+'.js', 'wb'))
        return self.yieldData(response, cache_file=open(cache_file, 'wb'))

    def __call__(self, env, start_response):
        req = webob.Request(env)
        return self._rewrite(req, start_response)


if __name__ == '__main__':
    if not os.path.isdir(CACHE_DIR):
        os.mkdir(CACHE_DIR)

    monkey.patch_all()
    handler = Proxy(pypiHost='pypi.python.org:80')

    wsgi.WSGIServer((host, port), handler).serve_forever()
    run()
