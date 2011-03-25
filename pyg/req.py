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
from .utils import ext
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
        w = WebManager(self)
        success = False
        for v, name, hash, url in w.find():
            if name.endswith('.egg'):
                vcode = 'py{0}'.format('.'.join(map(str, sys.version_info[:2])))
                if vcode not in name:
                    continue
            e = ext(name)
            if e not in ('.tar.gz', '.tar.bz2', '.zip', '.egg'):
                continue
            logger.info('Best match: {0}=={1}'.format(self.name, v))
            logger.info('Downloading {0}'.format(self.name))
            fobj = cStringIO.StringIO(WebManager.request(url))
            logger.info('Checking md5 sum')
            if md5(fobj.getvalue()).hexdigest() != hash:
                logger.fatal('E: {0} appears to be corrupted'.format(self.name))
                return
            if e in ('.tar.gz', '.tar.bz2', '.zip'):
                installer = Archive(fobj, e, w.name, self.reqset)
            elif e == '.egg':
                installer = Egg(fobj, name, self.reqset, w.name)

            ## There is no need to catch the exceptions now, this will be done by `pyg.inst.Installer.install`
            installer.install()
            if not self.version:
                self.version = v
            success = True
            break
        if not success:
            raise InstallationError