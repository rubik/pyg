import urllib2
import operator
import urlparse
import pkg_resources

from hashlib import md5

from pyg.utils import ext, right_egg, is_windows
from pyg.web import ReqManager, get_links, download
from pyg.core import Version, Egg, Archive, Binary, ReqSet, InstallationError, args_manager
from pyg.log import logger


__all__ = ['Requirement', 'WINDOWS_EXT']


WINDOWS_EXT = ('.exe', '.msi') if is_windows() else ()


class Requirement(object):

    OPMAP = {'==': operator.eq,
             '>=': operator.ge,
             '>': operator.gt,
             '<=': operator.le,
             '<': operator.lt,
             '!=': lambda a,b: a != b,
              None: lambda a,b: True, ##FIXME: does None really work?
             }

    version = op = None

    def __init__(self, req):
        self.req = req
        self._specs = pkg_resources.Requirement.parse(req).specs
        ## When no operator is specified
        if not self._specs:
            self._specs = [(None, None)]
            self.is_dev = None
        else:
            self.is_dev = any('dev' in v for op, v in self._specs)
        # version and op will be set after a call to ReqManager is made
        self.name, _, _ = self.split(req)
        self.reqset = ReqSet(self)
        self.package_index = args_manager['install']['index_url']

    def __repr__(self):
        return 'Requirement({0})'.format(self.req)

    def __str__(self):
        if self.version:
            return '{0}=={1}'.format(self.name, self.version)
        return str(self.req)

    def __eq__(self, other):
        return self.name == other.name and self.match(other.version)

    @staticmethod
    def split(chunk):
        for c in ('==', '>=', '>', '<=', '<', '!='):
            if c in chunk:
                name, op, version = map(str.strip, chunk.partition(c))
                version = Version(version)
                break
        else:
            name = chunk.split()[0]
            op = version = None
        return name, op, version

    def match(self, v):
        if v is None:
            return True
        return all(self.OPMAP[op](v, Version(version)) for op, version in self._specs)

    #def best_match(self, reqs):
    #    matched = {}
    #    for r in reqs:
    #        parts = r.split('-')
    #        version = Requirement.find_version('-'.join(parts[1:]))
    #        if self.version is None or self.match(version):
    #            matched[version] = r
    #    if len(matched) == 0:
    #        return None
    #    elif len(matched) == 1:
    #        return matched[matched.keys()[0]]
    #    ## The highest version possible
    #    return matched[max(matched)] ## OR matched[sorted(matched.keys(), reverse=True)[0]]?

    def _install_from_links(self, package_index):
        logger.info('Looking for links on {0}', package_index)
        try:
            links = get_links(self, package_index)
            if not links:
                raise InstallationError('Error: did not find any files')
        except Exception as e:
            raise InstallationError(str(e))
        logger.indent = 8
        for url in links:
            filename = urlparse.urlparse(url).path.split('/')[-1]
            logger.info('Found: {0}', filename)
            try:
                self._download_and_install(url, filename, self.name, ext(filename))
            except Exception as e:
                logger.error('Error: {0}', e)
                continue
            break
        logger.indent = 0
        if not self.success:
            raise InstallationError('Fatal: cannot install {0}'.format(self.name))

    def _check_bad_eggs(self, bad_eggs):
        ## Bad eggs are eggs which require a different Python version.
        ## If we don't find anything more, we check bad eggs.
        txt = 'Found only eggs for another Python version, which one do you want to install'
        choice = logger.ask(txt, choices=dict((v[1], v) for v in bad_eggs))
        self._download_and_install(*choice)

    def _download_and_install(self, url, filename, packname, e, hash=None):
        fobj = download(url, 'Downloading {0}'.format(self.name))
        if hash is not None:
            logger.info('Checking md5 sum')
            if md5(fobj.getvalue()).hexdigest() != hash:
                logger.fatal('Error: {0} appears to be corrupted', self.name)
                return
        if e in ('.tar.gz', '.tar.bz2', '.zip'):
            installer = Archive(fobj, e, packname, self.reqset)
        elif e == '.egg':
            installer = Egg(fobj, filename, self.reqset, packname)
        elif is_windows() and e in WINDOWS_EXT:
            installer = Binary(fobj, e, packname)
        else:
            logger.error('Error: unknown filetype: {0}', e, exc=InstallationError)

        ## There is no need to catch exceptions now, this will be done by `pyg.inst.Installer.install`
        installer.install()
        self.success = True

    def install(self):
        self.success = False
        logger.info('Looking for {0} releases on PyPI', self.name)
        p = ReqManager(self)
        try:
            files = p.files()
        except (urllib2.URLError, urllib2.HTTPError) as e:
            raise InstallationError(repr(e.reason) if hasattr(e, 'reason') else e.msg)
        bad_eggs = []
        for pext in ('.tar.gz', '.tar.bz2', '.zip', '.egg') + WINDOWS_EXT:
            for v, name, hash, url in files[pext]:
                if pext == '.egg' and not right_egg(name):
                    if args_manager['install']['force_egg_install']:
                        bad_eggs.append((url, name, p.name, pext, hash))
                    continue
                logger.info('Best match: {0}=={1}', self.name, v)
                try:
                    self._download_and_install(url, name, p.name, pext, hash)
                except InstallationError:
                    logger.info('Trying another file (if there is one)...')
                    continue
                if not self.version:
                    self.version = v
                break
            if self.success:
                return
        if bad_eggs:
            self._check_bad_eggs(bad_eggs)
        if not self.success:
            raise InstallationError('Error: Cannot find files available for dowloading and installing')
