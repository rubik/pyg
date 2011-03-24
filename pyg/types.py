import os
import re
import sys
import pkg_resources

from .utils import EASY_INSTALL, INSTALL_DIR, BIN, TempDir, TarFile, ZipFile, call_setup, name_from_egg, glob
from .scripts import script_args
from .log import logger



class InstallationError(Exception):
    pass

class AlreadyInstalled(InstallationError):
    pass

#class Version(object): ## OLD!! Does not work properly!
#    def __init__(self, v):
#        self.v = v
#        while self.v[-1] == 0:
#            self.v = self.v[:-2]
#
#    def __str__(self):
#        return self.v
#
#    def __repr__(self):
#        return 'Version({0})'.format(self.v)
#
#    def __eq__(self, other):
#        if len(self.v) != len(other.v):
#            return False
#        return self.v == other.v
#
#    def __ge__(self, other):
#        return self.v >= other.v
#
#    def __gt__(self, other):
#        return self.v > other.v
#
#    def __le__(self, other):
#        return self.v <= other.v
#
#    def __lt__(self, other):
#        return self.v < other.v


class Version(object):
    def __init__(self, v):
        self._v = v
        self.v = pkg_resources.parse_version(v)

    def __repr__(self):
        return 'Version({0})'.format(self._v)

    def __str__(self):
        return self._v

    def __eq__(self, o):
        return self.v == o.v

    def __ge__(self, o):
        return self.v >= o.v

    def __gt__(self, o):
        return self.v > o.v

    def __le__(self, o):
        return self.v <= o.v

    def __lt__(self, o):
        return self.v < o.v


class ReqSet(object):
    def __init__(self):
        self._reqs = set()

    def __iter__(self):
        for r in self.reqs:
            yield r

    def __nonzero__(self):
        return bool(self.reqs)

    def __bool__(self):
        return bool(self.reqs)

    def add(self, r):
        self._reqs.add(r)

    @ property
    def reqs(self):
        return self._reqs


class Egg(object):
    def __init__(self, fobj, eggname, reqset, packname=None):
        self.fobj = fobj
        self.eggname = os.path.basename(eggname)
        self.reqset = reqset
        self.packname = packname or name_from_egg(eggname)
        self.idir = INSTALL_DIR

    def install(self):
        eggpath = os.path.join(self.idir, self.eggname)
        if os.path.exists(eggpath):
            logger.info('{0} is already installed'.format(self.packname))
            raise AlreadyInstalled
        logger.info('Installing {0} egg file'.format(self.packname))
        with ZipFile(self.fobj) as z:
            z.extractall(eggpath)
        with open(EASY_INSTALL) as f: ## TODO: Fix the opening mode to read and write simultaneously
            lines = f.readlines()
        with open(EASY_INSTALL, 'w') as f:
            try:
                f.writelines(lines[:-1])
                f.write('./' + self.eggname + '\n')
                f.write(lines[-1])
            ## When using this file for the first time
            except IndexError:
                pass
        try:
            with open(os.path.join(eggpath, 'EGG-INFO', 'requires.txt')) as f:
                for line in f:
                    self.reqset.add(line.strip())
        except IOError:
            pass
        dist = pkg_resources.get_distribution(self.packname)
        for name, content, mode in script_args(dist):
            logger.info('Installing {0} script to {1}'.format(name, BIN))
            target = os.path.join(BIN, name)
            with open(target, 'w' + mode) as f:
                f.write(content)
                os.chmod(target, 0755)


class Archive(object):
    def __init__(self, fobj, ext, name, reqset):
        self.name = name
        if ext == '.zip':
            self.arch = ZipFile(fobj)
        else:
            self.arch = TarFile(fileobj=fobj, mode='r:{0}'.format(ext[1:]))
        self.reqset = reqset

    def install(self):
        with TempDir() as tempdir:
            with self.arch as a:
                a.extractall(tempdir)
            fullpath = os.path.join(tempdir, os.listdir(tempdir)[0])
            logger.info('Running setup.py egg_info for {0}'.format(self.name))
            if call_setup(fullpath, ['egg_info', '--egg-base', tempdir]) != 0:
                logger.fatal('E: Cannot run egg_info: package requirements will not be installed.')
                while True:
                    u = raw_input('Do you want to continue anyway? (y/[n]) ').lower()
                    if u in ('n', ''):
                        raise InstallationError
                    elif u == 'y':
                        break
            try:
                with open(os.path.join(glob(tempdir, '*.egg-info')[0], 'requires.txt')) as f:
                    for line in f:
                        self.reqset.add(line.strip())
            except IOError:
                pass
            logger.info('Running setup.py install for {0}'.format(self.name))
            if call_setup(fullpath, ['install', '--single-version-externally-managed',
                                     '--record', '.pyg-install-record']) != 0:
                logger.fatal('E: setup.py did not installed {0}'.format(self.name))
                raise InstallationError


class Bundle(object):
    def __init__(self, filepath):
        self.path = os.path.abspath(filepath)

    def install(self):
        with TempDir() as tempdir:
            with ZipFile(self.path) as z:
                z.extractall(tempdir)
            location = os.path.join(tempdir, 'build')
            pip_manifest = os.path.join(tempdir, 'pip-manifest.txt')
            with open(pip_manifest) as pf:
                lines = pf.readlines()[4:]
                main_pack, deps = [], []
                current = main_pack
                for line in lines:
                    if line.startswith('#'):
                        current = deps
                        continue
                    current.append(line.split('==')[0])
            logger.info('Installing dependencies')
            logger.indent += 8
            for d in deps:
                l = os.path.join(location, d)
                logger.info('Calling setup.py for {0}'.format(d))
                call_setup(l)
                logger.info('{0}: installed'.format(d))
            logger.indent = 0
            logger.info('Finished processing dependencies')
            logger.info('Installing main package')
            for p in main_pack:
                l = os.path.join(location, p)
                logger.info('Calling setup.py for {0}'.format(p))
                call_setup(l)
            logger.info('Bundle installed successfully')