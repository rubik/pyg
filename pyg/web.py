import re
import os
import time
import urllib
import urllib2
import urlparse
import cStringIO
import collections
import pkg_resources

from setuptools.package_index import PackageIndex
from pkgtools.pypi import PyPIXmlRpc, PyPIJson, real_name

from pyg.core import Version, args_manager
from pyg.utils import name, ext, right_egg, version_egg, is_windows
from pyg.log import logger


__all__ = ['PREFERENCES', 'ReqManager', 'get_versions', 'get_links', \
           'highest_version', 'request']


## This constant holds files priority
PREFERENCES = ('.tar.gz', '.tar.bz2', '.zip', '.egg')
if is_windows():
    PREFERENCES = ('.exe', '.msi') + PREFERENCES


def get_versions(req):
    '''
    Return all versions the given requirement can match.
    For example, if requirement is `pyg>=0.6` it will return: [0.6, 0.7].
    When a package has no files on PyPI (but at least a release) we have to
    look for version manually, with regular expressions.
    `req` should be a Requirement object (from pyg.core).
    '''

    if req.is_dev:
        return iter((Version('dev'),))
    _version_re = r'{0}-([\d\w.-]*).*'
    name = req.name
    pypi = PyPIXmlRpc()
    versions = map(Version, pypi.package_releases(name, True))

    ## Slow way: we need to search versions by ourselves
    if not versions:
        _vre = re.compile(_version_re.format(name), re.I)
        data = request((args_manager['install']['packages_url']+'/{0}').format(name))
        versions = map(Version, set(v.strip('.') for v in _vre.findall(data)))
    return (v for v in versions if req.match(v))

def highest_version(req):
    '''Return the highest version the given requirement can match.'''

    return max(get_versions(req))

def request(url):
    '''Perform a GET request to `url`.'''

    return urllib2.urlopen(url).read()

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

def format_time(seconds):
    if seconds == '':
        return ''
    hours, minutes = seconds // 3600, seconds // 60
    seconds -= int(3600 * hours + 60 * minutes)
    if minutes:
        if hours:
            return '{0:02d}h {1:02d}m {2:02d}s remaining'.format(*map(int, [hours, minutes, seconds]))
        return '{0:02d}m {1:02d}s remaining'.format(*map(int, [minutes, seconds]))
    return '{0:02d}s remaining'.format(int(seconds))

def download(url, msg, add_remaining=True):
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

        ## When the last block makes the downloaded size greater than the total size
        if ratio > 1:
            ratio = 1
            downloaded = total_size

        ## Calculate elapsed and remaining time
        elapsed = func() - starttime
        speed = downloaded / float(elapsed)
        try:
            remaining = (total_size - downloaded) / float(speed)
        except ZeroDivisionError:
            remaining = ''
        if ratio == 1:
            ## When we finish the download we want this string to hide
            remaining = ''

        if add_remaining:
            logger.info('\r{0} [{1:.0%} - {2} / {3}] {4}', msg, ratio, convert_bytes(downloaded),
                        convert_bytes(total_size), format_time(remaining), addn=False)
        else:
            logger.info('\r{0} [{1:.0%} - {2} / {3}]', msg, ratio, convert_bytes(downloaded),
                        convert_bytes(total_size), addn=False)

    if is_windows():
        ## On Windows time.clock should be more precise.
        func = time.clock
    else:
        func = time.time
    starttime = func()
    path = urllib.urlretrieve(url, reporthook=hook)[0]
    logger.newline()
    with open(path) as f:
        return cStringIO.StringIO(f.read())


class ReqManager(object):

    _pkg_re = re.compile('(?P<package_name>[\w][\w\d]+)-'              # alphanumeric / underscore + alphanumeric / digit / underscore
                         '(?P<version>\d[\d\w.]+)'                     # digit + digit / dot / alphanumeric
                         '.*?'                                         # anything
                         '(?P<ext>\.(?:tar\.gz|tar\.bz2|zip|egg|tgz))' # the extension
    )

    def __init__(self, req, pref=None):
        self.req = req
        self.req.name = self.name = real_name(self.req.name)
        if self.req.op == '==': ## LOL
            self.package_manager = PyPIJson(self.name, self.req.version)
        else:
            hi = highest_version(self.req)
            self.req.version = hi
            self.package_manager = PyPIJson(self.name, hi)

        url = args_manager['install']['index_url'] + '/' + self.package_manager.URL.split('/pypi/', 1)[1]
        self.package_manager.URL = url
        self._set_prefs(pref)
        self.downloaded_name = None
        self.downloaded_version = None

    def _set_prefs(self, pref):
        if pref is None:
            pref = PREFERENCES
        pref = list(pref)
        if len(pref) < len(PREFERENCES):
            for p in PREFERENCES:
                if p not in pref:
                    pref.append(p)
        self.pref = pref

    def _setuptools_find(self):
        def _get_all(url):
            match = self._pkg_re.search(url)
            if match is None:
                return None, None, None
            return map(match.group, ('package_name', 'version', 'ext'))
        def _remove_query(url):
            return urlparse.urlunsplit(urlparse.urlsplit(url)[:3] + ('',) * 2)
        def _get_version(filename):
            ## A bit hacky but there is no solution because some packages
            ## are in the form {package_name}-{version}-{something_else}-{?pyx.y}.{ext}
            ## and we cannot predict where is the version in that mess.
            _version_re = re.compile(r'[\d\w.]*')
            parts = name(filename).split('-')
            for part in parts:
                match = _version_re.search(part)
                if match is not None:
                    return match.group()

        logger.warn('Warning: did not find any files on PyPI')
        found = []
        for link in get_links(str(self.req), args_manager['install']['packages_url']):
            package_name = _remove_query(link).split('/')[-1]
            version = _get_version(package_name)
            e = ext(package_name)
            if package_name is None or version is None:
                package_name, version, e = _get_all(link)
            found.append((version, package_name, None, link, e))
        return found

    def find(self):
        if self.req.is_dev:
            links = get_links(str(self.req))
            return [('dev', self.req.name, None, link, ext(link)) for link in links]
        return list(self.package_manager.find()) or self._setuptools_find()

    def files(self):
        files = collections.defaultdict(list)
        for release in self.find():
            e = release[-1]
            if e not in self.pref:
                logger.debug('debug: Skipping {0}, unknown extension', release[-2])
            files[e].append(release[:-1])
        return files

    def download(self, dest):
        """ you can set dest to None, it will executed a try run """
        if dest:
            dest = os.path.abspath(dest)
        files = self.files()
        downloaded = []

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
                if dest:
                    try:
                        data = download(url, 'Retrieving data for {0}'.format(self.name)).getvalue()
                    except (urllib2.URLError, urllib2.HTTPError) as e:
                        logger.debug('urllib2 error: {0}', e.args)
                        continue
                    if not data:
                        logger.debug('debug: Request failed')
                        continue
                    if not os.path.exists(dest):
                        os.makedirs(dest)
                    try:
                        # Fix for packages with no version in the name
                        if '-' not in name:
                            name = '{0}-{1}{2}'.format(name, v, p)
                        logger.info('Writing data into {0}', name)
                        with open(os.path.join(dest, name), 'w') as f:
                            f.write(data)
                    except (IOError, OSError):
                        logger.debug('debug: Error while writing data')
                        continue
                downloaded.append({'url': url, 'hash': hash})
                logger.success('{0} downloaded successfully', self.name)
                success = True
            self.downloaded_name = name
            self.downloaded_version = v

        return downloaded


class PygPackageIndex(PackageIndex):
    '''
    Pyg's own PackageIndex derived from setuptools' one. This PackageIndex does
    not download any files but crawl the index looking for links available for
    the download.
    '''

    def __init__(self, *a, **k):
        PackageIndex.__init__(self, *a, **k)
        self.urls = set()

    def _download_to(self, url, filename):
        self.urls.add(url)
        return

    def download(self, spec, tmpdir=None):
        self.urls.add(spec)
        return


def get_links(package, index_url=None):
    ## Correction for standard installations when index_url looks standard
    ## http://pypi.python.org/pypi.
    if index_url is None:
        index_url = args_manager['install']['packages_url']
    logger.info('Looking for packages at {0}', index_url)
    urls = set()
    package_index = PygPackageIndex(index_url)
    req = pkg_resources.Requirement.parse(str(package))
    for source in (True, False):
        package_index.fetch_distribution(req, None, force_scan=True, \
                                             source=source, develop_ok=False)
        for url in package_index.urls:
            ## PackageIndex looks for local distributions too, and we
            ## don't want that.
            if url.startswith(('http', 'https')):
                urls.add(urlparse.urldefrag(url)[0])
    return urls


## OLD! We are using Json to interoperate with pypi.
## We use it only if we don't find any files with the Json API
## UPDATE: Now we use PyPIJson (from pktools) in combination with get_links
## (from setuptools).
##
## Old link finder we used to retrieve packages' links.
## Now we use setuptools' PackageIndex and PyPI Json API.
## (above)
##
##
#######################################################################
#
#class LinkFinder(object):
#
#    INDEX = None
#    FILE = r'href\s?=\s?("|\')(?P<file>.*{0}-{1}\.(?:tar\.gz|tar\.bz2|zip|egg))(?:\1)'
#    LINK = r'<a\s?href="(?P<href>[^"]+)"\srel="(?P<rel>[^"]+)">(?P<version>[\d\.]+[\w^.]+)(?P<name>[^\<]+)</a><br/>'
#    SIMPLE_LINK = r'<a\shref="(?P<href>[^"]+)">(?P<name>[^<]+)</a>'
#
#    def __init__(self, package_name, index=None):
#        self.package_name = package_name
#        if index is None:
#            index = 'http://pypi.python.org/simple/'
#        if not index.endswith('/'):
#            index += '/'
#        self.INDEX = index
#
#    def _check_link(self, link, version):
#        '''
#        Check whether the link is good or not. The link must satisfy the following conditions:
#
#            * It have to end with a right extension (.tar.gz, .tar.bz2, .zip, or .egg).
#            * It have to be the newest (i.e. the version must be the one specified).
#        '''
#
#        base = link.split('/')[-1]
#        e = ext(base)
#        if e not in ('.tar.gz', '.tar.bz2', '.zip', '.egg'):
#            return False
#        return '{0}-{1}{2}'.format(self.package_name, version, e) == base
#
#    def find_best_link(self):
#        data = request('{0}{1}'.format(self.INDEX, self.package_name))
#        d = {}
#        for href, name in re.compile(self.SIMPLE_LINK).findall(data):
#            e = ext(name)
#            if e in ('.tar', '.tar.gz', '.tar.bz2', '.zip'):
#                version = name.split('-')[-1][:-len(e)]
#            elif e in ('.exe', '.msi'):
#                version = '.'.join(name.split('-')[-2].split('.')[:-1])
#            else:
#                try:
#                    version = pkg_resources.Distribution.from_filename(name).version
#                except ValueError:
#                    logger.debug('debug: Failed to find version for {0}, continuing...', name)
#                    continue
#            if not href.startswith('http'):
#                href = '/'.join([self.INDEX, self.package_name, href])
#            d[Version(version)] = href
#        for href, rel, version, name in re.compile(self.LINK).findall(data):
#            if rel == 'download':
#                d[Version(version)] = href
#
#        ## Find highest version and returns its link
#        try:
#            v = max(d)
#            return v, d[v]
#        except ValueError:
#            return None, None
#
#    def find_files(self, url, version):
#        url = url + '/'[:not url.endswith('/')]
#        base = '{0}://{1}/'.format(*urlparse.urlparse(url)[:2])
#        logger.info('Reading {0}', url)
#
#        ## This is horrible, but there is no alternative...
#        ## We cannot use standard regex because on external sites HTML can be
#        ## different and we would run up against problems.
#        data = request(url).split('</a>')
#        links = set()
#        for item in data:
#            if 'href' in item:
#                i = item.index('href="')
#                item = item[i + 6:]
#                link = item[:item.index('">')]
#                if not link.startswith('http'):
#                    link = base + link
#                links.add(link)
#        return [l for l in links if self._check_link(l, version)]
#
#    def find(self):
#        version, link = self.find_best_link()
#        if version is None:
#            raise PygError('Error: did not find any files')
#        link = urlparse.urldefrag(link)[0]
#        if ext(link) in PREFERENCES:
#            return [link]
#        return self.find_files(link, version)
