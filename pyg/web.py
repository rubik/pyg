import re
import os
import time
import urllib
import urllib2
import httplib2
import urlparse
import cStringIO
import posixpath
import pkg_resources

from pkgtools.pypi import PyPIXmlRpc, PyPIJson, real_name

from pyg.core import PygError, Version
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
    h = httplib2.Http('.cache')
    resp, content = h.request(url)
    if resp['status'] == '404':
        logger.error('Error: URL does not exist: {0}', url, exc=PygError)
    return content

def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '{0:.1f} Tb'.format(terabytes)
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '{0:.1f} Gb'.format(gigabytes)
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '{0:.1f} Mb'.format(megabytes)
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '{0:.1f} Kb'.format(kilobytes)
    else:
        size = '{0:.1f} b'.format(bytes)
    return size

def download(url, msg):
    def average(sample):
        n = len(sample)
        if n == 1:
            return sample[0]
        return sum(sample, .1) / (n - 1)
    def hook(blocks, block_size, total_size):
        '''
        Callback function for `urllib.urlretrieve` that is called when connection is
        created and then once for each block.

        Display the amount of data transferred so far and it percentage.

        Use sys.stdout.write() instead of "print,", because it allows one more
        symbol at the line end without linefeed on Windows

        :param blocks: Number of blocks transferred so far.
        :param block_size: Size of each block in bytes.
        :param total_size: Total size of the HTTP object in bytes. Can be -1 if server doesn't return it.
        '''

        if block_size > total_size:
            logger.info('\r{0} [100% - {1}]', msg, convert_bytes(total_size), addn=False)
            return
        downloaded = block_size * blocks
        ratio = downloaded / float(total_size)

        ## Calculate download speed
        speed = downloaded / float(func() - starttime)
        times.append(speed)

        ## When the last block makes the downloaded size greater than the total size
        if ratio > 1:
            ratio = 1
        logger.info('\r{0} [{1:.0%} - {2} / {3}] {4}/s', msg, ratio, \
                    *map(convert_bytes, [downloaded, total_size, average(times)]), addn=False)

    if is_windows():
        func = time.clock
    else:
        func = time.time
    starttime = func()
    times = []
    path = urllib.urlretrieve(url, reporthook=hook)[0]
    logger.newline()
    with open(path) as f:
        return cStringIO.StringIO(f.read())


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
        self.package_manager._request_func = request

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
                    data = download(url, 'Retrieving data for {0}'.format(self.name)).getvalue()
                except (urllib2.URLError, urllib2.HTTPError) as e:
                    logger.debug('urllib2 error: {0}', e.args)
                    continue
                if not data:
                    logger.debug('request failed')
                    continue
                if not os.path.exists(dest):
                    os.makedirs(dest)
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
    LINK = r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<version>[\d\.]+[\w^.]+)(?P<name>[^\<]+)</a><br/>'
    SIMPLE_LINK = r'<a\shref="(?P<href>[^"]+)">(?P<name>[^<]+)</a>'

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
        for href, name in re.compile(self.SIMPLE_LINK).findall(data):
            e = ext(name)
            if e in ('.tar', '.tar.gz', '.tar.bz2', '.zip'):
                version = name.split('-')[-1][:-len(e)]
            elif e in ('.exe', '.msi'):
                version = '.'.join(name.split('-')[-2].split('.')[:-1])
            else:
                try:
                    version = pkg_resources.Distribution.from_filename(name).version
                except ValueError:
                    logger.debug('debug: Failed to find version for {0}, continuing...', name)
                    continue
            if not href.startswith('http'):
                href = '/'.join([self.INDEX, self.package_name, href])
            d[Version(version)] = href
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
        url = url + '/'[:not url.endswith('/')]
        base = '{0}://{1}/'.format(*urlparse.urlparse(url)[:2])
        logger.info('Reading {0}', url)

        ## This is horrible, but there is no alternative...
        ## We cannot use standard regex because on external sites HTML can be
        ## different and we would run up against problems.
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
        link = urlparse.urldefrag(link)[0]
        if ext(link) in PREFERENCES:
            return [link]
        return self.find_files(link, version)