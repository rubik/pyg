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

from .utils import ext, right_egg
from .web import WebManager, PackageManager
from .types import Version, Egg, Archive, ReqSet
from .log import logger



class Requirement(object):

    OPMAP = {'==': operator.eq,
             '>=': operator.ge,
             '>': operator.gt,
             '<=': operator.le,
             '<': operator.lt,
             None: lambda a,b: True
             }

    def __init__(self, req):
        self.req = req
        self.reqset = ReqSet()
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
        return self.OPMAP[self.op](v, self.version)

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
        p = PackageManager(self)
        success = False
        for pext in ('.tar.gz', '.tar.bz2', '.zip', '.egg'):
            for v, name, hash, url in p.arrange_items()[pext]:
                if pext == '.egg' and not right_egg(name):
                    continue
                e = ext(name)
                if e not in ('.tar.gz', '.tar.bz2', '.zip', '.egg'):
                    continue
                logger.info('Best match: {0}=={1}', self.name, v)
                logger.info('Downloading {0}', self.name)
                fobj = cStringIO.StringIO(WebManager.request(url))
                logger.info('Checking md5 sum')
                if md5(fobj.getvalue()).hexdigest() != hash:
                    logger.fatal('E: {0} appears to be corrupted', self.name)
                    return
                if e in ('.tar.gz', '.tar.bz2', '.zip'):
                    installer = Archive(fobj, e, p.name, self.reqset)
                elif e == '.egg':
                    installer = Egg(fobj, name, self.reqset, p.name)
    
                ## There is no need to catch the exceptions now, this will be done by `pyg.inst.Installer.install`
                installer.install()
                if not self.version:
                    self.version = v
                success = True
                break
            if success:
                break
        if not success:
            raise InstallationError