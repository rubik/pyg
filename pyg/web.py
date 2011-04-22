import re
import os
import urllib2

from pkgtools.pypi import PyPIXmlRpc, PyPIJson, real_name

from pyg.types import PygError, Version, args_manager
from pyg.utils import FileMapper, ext, right_egg, version_egg
from pyg.log import logger


__all__ = ['ReqManager', 'get_version', 'request', 'PREFERENCES']


## This constants holds files priority
PREFERENCES = ('.egg', '.tar.gz', '.tar.bz2', '.zip')


def get_versions(req):
    _versions_re = r'{0}-(\d+\.?(?:\d\.?|\d\w)*)-?.*'
    name = req.name
    pypi = PyPIXmlRpc()
    versions = map(Version, self.pypi.package_releases(self.name, True))

    ## Slow way: we need to search versions by ourselves
    if not versions:
        _vre = re.compile(_versions_re.format(name), re.I)
        data = request('http://pypi.python.org/simple/{0}'.format(name))
        versions = map(Version, set(v.strip('.') for v in _vre.findall(data)))
    return (v for v in versions if req.match(v))

def highest_version(req):
    return max(get_versions(req))

def request(url):
    r = urllib2.Request(url)
    return urllib2.urlopen(r).read()


class ReqManager(object):
    def __init__(self, req, pref=None):
        self.req = req
        self.req.name = self.name = real_name(self.req.name)
        if self.req.op is None:
            self.package_manager = PyPIJson(self.name)
        elif self.req.op == '==': ## LOL
            self.package_manager = PyPIJson(self.name, self.req.version)
        else:
            self.package_manager = PyPIJson(self.name, get_version(self.req))

        self._set_prefs(pref)

    def _set_prefs(self, pref):
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
                    data = request(url)
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


## OLD! We are using xmlrpclib to communicate with pypi.
## Maybe we can use it in the future.
class LinkFinder(object):

    base_url = 'http://pypi.python.org/simple/'
    file_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)">(?P<name>[^\<]+)</a><br/>')
    link_regex = re.compile(r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<name>[^\<]+)</a><br/>')
