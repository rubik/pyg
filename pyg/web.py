import re
import os
import urllib2
import urlparse

from pkgtools.pypi import PyPIXmlRpc, PyPIJson, real_name

from pyg.core import PygError, Version, args_manager
from pyg.utils import FileMapper, ext, right_egg, version_egg, is_windows
from pyg.log import logger


__all__ = ['PREFERENCES', 'ReqManager', 'LinkFinder', 'get_versions', \
           'highest_version', 'request']


## This constants holds files priority
PREFERENCES = ('.egg', '.tar.gz', '.tar.bz2', '.zip')
if is_windows():
    PREFERENCES = ('.exe', '.msi') + PREFERENCES


def get_versions(req):
    _versions_re = r'{0}-(\d+\.?(?:\d\.?|\d\w)*)-?.*'
    name = req.name
    pypi = PyPIXmlRpc()
    versions = map(Version, pypi.package_releases(name, True))

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
            self.package_manager = PyPIJson(self.name, highest_version(self.req))

        self._set_prefs(pref)

    def _set_prefs(self, pref):
        if pref is None:
            pref = PREFERENCES
        pref = list(pref)
        if len(pref) < len(PREFERENCES):
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


## OLD! We are using Json to interoperate with pypi.
## We use it only if we don't find any files with the Json API
class LinkFinder(object):

    INDEX = None
    FILE = r'href\s?=\s?("|\')(?P<file>.*{0}-{1}\.(?:tar\.gz|tar\.bz2|zip|egg))(?:\1)'
    LINK = r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<version>[\d\.-]+)(?P<name>[^\<]+)</a><br/>'

    def __init__(self, package_name, index=None):
        self.package_name = package_name
        if index is None:
            index = 'http://pypi.python.org/simple/'
        if not index.endswith('/'):
            index += '/'
        self.INDEX = index

    def _check_link(self, link, version):
        '''
        Check whether the link is good or not. The link must satisfy the following conditions:

            * It have to end with a right extension (.tar.gz, .tar.bz2, .zip, or .egg).
            * It have to be the newest (i.e. the version must be the one specified).
        '''

        base = link.split('/')[-1]
        e = ext(base)
        if e not in ('.tar.gz', '.tar.bz2', '.zip', '.egg'):
            return False
        return '{0}-{1}{2}'.format(self.package_name, version, e) == base

    def find_best_link(self):
        data = request('{0}{1}'.format(self.INDEX, self.package_name))
        d = {}
        for href, rel, version, name in re.compile(self.LINK).findall(data):
            if rel == 'download':
                d[Version(version)] = href

        ## Find highest version and returns its link
        try:
            v = max(d)
            return v, d[v]
        except ValueError:
            return None, None

    def find_files(self, url, version):
        if ext(url) in PREFERENCES:
            return [url]
        url = url + '/'[:not url.endswith('/')]
        base = '{0}://{1}/'.format(*urlparse.urlparse(url)[:2])
        logger.info('Reading {0}', url)
        ## This is horrible, but there is no alternative...
        data = request(url).split('</a>')
        links = set()
        for item in data:
            if 'href' in item:
                i = item.index('href="')
                item = item[i + 6:]
                link = item[:item.index('">')]
                if not link.startswith('http'):
                    link = base + link
                links.add(link)
        return [l for l in links if self._check_link(l, version)]

    def find(self):
        version, link = self.find_best_link()
        if version is None:
            raise PygError('Error: did not find any files')
        return self.find_files(link, version)