import re
import os.path
import urllib2
import xmlrpclib
import collections

from .req import Requirement, Version


__all__ = ['WebManager', 'PyPI', 'Finder']


class _FileMapper(collections.defaultdict):

    def __missing__(self, key):
        return self['others']


def PyPI(index_url='http://pypi.python.org/pypi'):
    return xmlrpclib.ServerProxy(index_url, xmlrpclib.Transport())


class WebManager(object):

    _versions_re = r'{0}-(\d+\.?(?:\d\.?|\d\w)*)-?.*'

    def __init__(self, name, index_url='http://pypi.python.org/pypi'):
        self.pypi = PyPI(index_url)
        self.r = Requirement(name)
        self.name = self.r.name
        self.versions = map(Version, self.pypi.package_releases(self.name, True))
        if not self.versions: ## Slow way: we need to search versions by ourselves
            self.versions = WebManager.version_from_html(self.name)

    @ staticmethod
    def request(url):
        r = urllib2.Request(url)
        return urllib2.urlopen(r).read()

    @ staticmethod
    def versions_from_html(name):
        _vre = re.compile(WebManager._versions_re.format(name), re.I)
        data = WebManager.request('http://pypi.python.org/simple/{0}'.format(name))
        return map(Version, set(v.strip('.') for v in _vre.findall(data)))

    def find(self):
        for version in self.versions:
            if self.r.match(version):
                for res in self.pypi.release_urls(self.name, str(version)):
                    yield version, res['filename'], res['md5_digest'], res['url']


class Finder(object): ## OLD! Now we are using xmlrpclib to communicate with pypi

    base_url = 'http://pypi.python.org/simple/'
    file_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)">(?P<name>[^\<]+)</a><br/>')
    link_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<name>[^\<]+)</a><br/>')

    def __init__(self, packname):
        self.url = '{0}{1}'.format(self.base_url, packname)

    def find(self):
        files = _FileMapper(list, {'.gz': {}, '.bz2': {}, '.zip': {},
                                  '.egg': {}, 'others': {}
                                 }
                           )

        print 'Checking: {0}'.format(self.url)
        data = request(self.url)
        f = self.file_regex.findall(data)
        links = self.link_regex.findall(data)
        for l, file in f:
            ext = os.path.splitext(file)[1]
            files[ext][file] = l
        return files, links