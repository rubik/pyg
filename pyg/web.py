import re
import os
import urllib2

from pkgtools.pypi import PyPIXmlRpc as PyPI
from .types import PygError, Version, args_manager
from .utils import FileMapper, ext, right_egg, version_egg
from .log import logger


__all__ = ['WebManager', 'PackageManager', 'PREFERENCES']


## This constants holds files priority
PREFERENCES = ('.egg', '.tar.gz', '.tar.bz2', '.zip')


class WebManager(object):

    _versions_re = r'{0}-(\d+\.?(?:\d\.?|\d\w)*)-?.*'

    def __init__(self, req):
        self.pypi = PyPI(index_url=args_manager['index_url'])
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

        self.versions = map(Version, self.pypi.package_releases(self.name, True))
        if not self.versions:
            self.name, old = self.name.capitalize(), self.name
            self.versions = map(Version, self.pypi.package_releases(self.name, True))
        ## Slow way: we need to search versions by ourselves
        if not self.versions:
            self.name = old
            self.versions = WebManager.versions_from_html(self.name)
        self.versions = sorted((v for v in self.versions if req.match(v)), reverse=True)

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
        self.name = self.w.name
        self.pref = pref
        self.files = FileMapper(list)
        self.files.pref = self.pref

    def arrange_items(self):
        for p in self.w.find():
            e = ext(p[3])
            self.files[e].append(p)
        ## FIXME: We have to consider the preferences!
        return self.files


class Downloader(object):
    def __init__(self, req, pref=None):
        try:
            self.pman = PackageManager(req, pref)
            self.name = self.pman.name
        except urllib2.HTTPError as e:
            logger.fatal('E: {0}', e.msg)
            raise PygError

        self.files = self.pman.arrange_items()
        if not self.files:
            logger.error('E: Did not find files to download')
            raise PygError

    def download(self, dest):
        dest = os.path.abspath(dest)

        ## We need a placeholder because of the nested for loops
        success = False

        for p in self.pman.pref:
            if success:
                break
            if not self.files[p]:
                logger.error('{0} files not found. Continue searching...', p)
                continue
            for v, name, hash, url in self.files[p]:
                if success:
                    break
                if p == '.egg' and not right_egg(name):
                    logger.info('Found egg file for another Python version: {0}. Continue searching...',                               version_egg(name))
                    continue
                try:
                    data = WebManager.request(url)
                except (urllib2.URLError, urllib2.HTTPError) as e:
                    logger.debug('urllib2 error: {0}', e.args)
                    continue
                if not data:
                    logger.debug('request failed')
                    continue
                if not os.path.exists(dest):
                    os.makedirs(dest)
                logger.info('Retrieving data for {0}', self.name)
                try:
                    logger.info('Writing data into {0}', name)
                    with open(os.path.join(dest, name), 'w') as f:
                        f.write(data)
                except (IOError, OSError):
                    logger.debug('error while writing data')
                    continue
                logger.info('{0} downloaded successfully', self.name)
                success = True
                self.name = name


## OLD! We are using xmlrpclib to communicate with pypi
## Maybe we can use it in the future
class LinkFinder(object):

    base_url = 'http://pypi.python.org/simple/'
    file_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)">(?P<name>[^\<]+)</a><br/>')
    link_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<name>[^\<]+)</a><br/>')