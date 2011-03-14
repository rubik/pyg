import os
import re
import sys
import operator
import cStringIO
import pkg_resources

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

from .web import WebManager
from .types import Version, Egg, Archive, InstallationError
from .log import logger



class Requirement(object):

    OPMAP = {'==': operator.eq,
             '>=': operator.ge,
             '>': operator.gt,
             '<=': operator.le,
             '<': operator.lt
             }

    def __init__(self, req):
        self.req = req
        self.split()

    def __repr__(self):
        return 'Requirement({0})'.format(self.req)

    def __str__(self):
        return str(self.req)

    def split(self):
        for c in ('==', '>=', '>', '<=', '<'):
            if c in self.req:
                self.name, self.op, self.version = map(str.strip, self.req.partition(c))
                self.version = Version(self.version)
                break
        else:
            self.name = self.req.split()[0]
            self.version = None
            self.op = None

    @ staticmethod
    def find_version(s):
        v = []
        for c in s:
            if c.isdigit() or c == '.':
                v.append(c)
            else:
                break
        return Version(''.join(v).strip('.')) ## FIXME do we really need .strip() ?

    def match(self, v):
        try:
            return self.OPMAP[self.op](v, self.version)
        except KeyError: ## Operator not specified, so we pick up any version
            return True

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

    def install(self):
        w = WebManager(self)
        try:
            for v, name, hash, url in w.find():
                if name.endswith('.egg'):
                    vcode = 'py{0}'.format('.'.join(map(str, sys.version_info[:2])))
                    if vcode not in name:
                        continue
                logger.notify('Downloading {0}'.format(self.name))
                fobj = cStringIO.StringIO(WebManager.request(url))
                logger.notify('Checking md5 sum')
                if md5(fobj.getvalue()).hexdigest() != hash:
                    logger.fatal('E: {0} appears to be corrupted'.format(self.name))
                    return
                ext = os.path.splitext(name)[1]
                if ext in ('.gz', '.bz2', '.zip'):
                    installer = Archive(fobj, ext, w.name)
                elif ext == '.egg':
                    installer = Egg(fobj, name, w.name)
                else:
                    continue
                try:
                    installer.install()
                    self.version = Version(v)
                except Exception as err:
                    logger.error('E: {0}'.format(err))
                break
            else:
                logger.fatal('E: Did not find files to install')
                raise InstallationError
        except Exception as e:
            logger.fatal('E: An error occurred while installing {0}'.format(w.name))
            raise InstallationError