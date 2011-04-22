import re
import os
import urllib2

from pkgtools.pypi import PyPIXmlRpc, PyPIJson, real_name

from pyg.types import PygError, Version, args_manager
from pyg.utils import FileMapper, ext, right_egg, version_egg
from pyg.log import logger


__all__ = ['WebManager', 'ReqManager', 'Json', 'PREFERENCES']


## This constants holds files priority
PREFERENCES = ('.egg', '.tar.gz', '.tar.bz2', '.zip')


class ReqManager(object):
    def __init__(self, req, pref=None):
        self.req = req
        if self.req.op is None:
            ## Use PyPI's Json interface
            ## to get some more speed

            self.package_manager = PyPIJson(self.req.name)
        else:
            self.package_manager = WebManager(self.req)
        self.name = self.req.name

        if pref is None:
            pref = PREFERENCES
        pref = list(pref)
        if len(pref) < 4:
            for p in PREFERENCES:
                if p not in pref:
                    pref.append(p)
        self.pref = pref

    def find(self):
        return self.package_manager.find()

    def files(self):
        files = FileMapper(list)
        files.pref = self.pref
        for release in self.find():
            files[ext(release[3])].append(release)
        return files

    def download(self, dest):
        dest = os.path.abspath(dest)
        files = self.files()

        ## We need a placeholder because of the nested for loops
        success = False

        for p in self.pref:
            if success:
                break
            if not files[p]:
                logger.warn('{0} files not found. Continue searching...', p)
                continue
            for v, name, hash, url in files[p]:
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
                self.downloaded_name = name
                self.downloaded_version = v


class WebManager(object):

    _versions_re = r'{0}-(\d+\.?(?:\d\.?|\d\w)*)-?.*'

    def __init__(self, req):
        self.pypi = PyPIXmlRpc(index_url=args_manager['index_url'])
        self.req = req
        try:
            self.name = real_name(self.req.name)
        except urllib2.HTTPError as e:
            logger.error(e.msg, exc=PygError)

        ## So the req can know the real name of the package
        self.req.name = self.name

        ## Try to use PyPI's XML-RPC API
        self.versions = map(Version, self.pypi.package_releases(self.name, True))

        ## Slow way: we need to search versions by ourselves
        if not self.versions:
            self.versions = WebManager.versions_from_html(self.name)
        self.versions = sorted((v for v in self.versions if self.req.match(v)), reverse=True)

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
        version = max(self.versions)
        for res in self.pypi.release_urls(self.name, str(version)):
            yield version, res['filename'], res['md5_digest'], res['url']


class Json(object):
    def __init__(self):
        self.cache = {}

    def json(self, package_name, fast=False):
        if package_name in self.cache:
            return self.cache[package_name]
        pypi = PyPIJson(package_name, fast)
        data = pypi.retrieve()
        self.cache[package_name] = data
        self.package_name = pypi.package_name
        return data


## OLD! We are using xmlrpclib to communicate with pypi.
## Maybe we can use it in the future.
class LinkFinder(object):

    base_url = 'http://pypi.python.org/simple/'
    file_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)">(?P<name>[^\<]+)</a><br/>')
    link_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<name>[^\<]+)</a><br/>')
