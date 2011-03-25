import re
import urllib2
import xmlrpclib

from .types import Version, args_manager
from .utils import FileMapper, ext


__all__ = ['WebManager', 'PackageManager', 'PyPI', 'PREFERENCES']


## This constants holds files priority
PREFERENCES = ('.egg', '.tar.gz', '.tar.bz2', '.zip')


def PyPI(index_url='http://pypi.python.org/pypi'):
    return xmlrpclib.ServerProxy(index_url, xmlrpclib.Transport())


class WebManager(object):

    _versions_re = r'{0}-(\d+\.?(?:\d\.?|\d\w)*)-?.*'

    def __init__(self, req):
        self.pypi = PyPI(args_manager['index_url'])
        self.req = req
        self.name = self.req.name
        self.versions = None
        try:
            realname = sorted(self.pypi.search({'name': self.name}),
                              key=lambda i: i['_pypi_ordering'], reverse=True)[0]['name']
            if self.name.lower() == realname.lower():
                self.name = realname
                req.name = realname
        except (KeyError, IndexError):
            pass

        self.versions = sorted(map(Version, self.pypi.package_releases(self.name, True)), reverse=True)
        if not self.versions:
            self.name, old = self.name.capitalize(), self.name
            self.versions = sorted(map(Version, self.pypi.package_releases(self.name, True)), reverse=True)
        ## Slow way: we need to search versions by ourselves
        if not self.versions:
            self.name = old
            self.versions = WebManager.versions_from_html(self.name)

    @ staticmethod
    def request(url):
        r = urllib2.Request(url)
        return urllib2.urlopen(r).read()

    @ staticmethod
    def versions_from_html(name):
        _vre = re.compile(WebManager._versions_re.format(name), re.I)
        data = WebManager.request('http://pypi.python.org/simple/{0}'.format(name))
        return sorted(map(Version, set(v.strip('.') for v in _vre.findall(data))), reverse=True)

    def find(self):
        for version in self.versions:
            if self.req.match(version):
                for res in self.pypi.release_urls(self.name, str(version)):
                    yield version, res['filename'], res['md5_digest'], res['url']


class PackageManager(object):
    def __init__(self, req, pref=None):
        if pref is None:
            pref = PREFERENCES
        if len(pref) < 4:
            for p in PREFERENCES:
                if p not in pref:
                    pref.append(p)

        ## For now fast=True and index_url=DEFAULT
        self.w = WebManager(req)
        self.pref = pref
        self.files = FileMapper(list)
        self.files.pref = self.pref

    def arrange_items(self):
        for p in self.w.find():
            e = ext(p[3])
            self.files[e].append(p)
        return self.files


## OLD! We are using xmlrpclib to communicate with pypi
## Maybe we can use it in the future
class LinkFinder(object):

    base_url = 'http://pypi.python.org/simple/'
    file_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)">(?P<name>[^\<]+)</a><br/>')
    link_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<name>[^\<]+)</a><br/>')