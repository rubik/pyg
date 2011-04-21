import os
import sys
import tarfile
import pkg_resources
import ConfigParser
from cStringIO import StringIO

from pkgtools.pkg import Dir as DirTools, EggDir
from pyg.scripts import script_args
from pyg.locations import EASY_INSTALL, INSTALL_DIR, BIN
from pyg.utils import TempDir, ZipFile, call_setup, run_setup, name_from_egg, glob, ext
from pyg.log import logger


## A generic error thrown by Pyg
class PygError(Exception):
    pass

## An error thrown when the installation goes wrong
class InstallationError(PygError):
    pass

## This isn't really an error but it is useful when Pyg is used as a library
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
    '''
    This class implements a Version object with comparison methods::

        >>> Version('0.1') < Version('0.1.1')
        True
        >>> Version('0.1') == Version('0.1')
        True
        >>> Version('0.1') >= Version('0.1')
        True
        >>> Version('0.1b') > Version('0.1')
        False
        >>> Version('0.1b') > Version('0.1a')
        True
    '''

    def __init__(self, v):
        self._v = v
        self.v = pkg_resources.parse_version(v)

    def __str__(self):
        return str(self._v)

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
    '''
    A requirement set, used by :class:`~pyg.types.Archive` and :class:`~pyg.types.Egg` to keep trace of package's requirements.
    '''

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
    '''
    This class represent a Python Egg object. It needs a file-like object with egg data.

    :param fobj: the file-like object with egg data
    :param eggname: the egg name (for example ``pyg-0.1.2-py2.7.egg``)
    :param reqset: a :class:`~pyg.types.ReqSet` object used to store requirements
    :param packname: the package name. If the egg name is ``pyg-0.1.2-py2.7.egg``, *packname* should be ``pyg``


    '''

    def __init__(self, fobj, eggname, reqset, packname=None):
        self.fobj = fobj
        self.eggname = os.path.basename(eggname)
        self.reqset = reqset
        self.packname = packname or name_from_egg(eggname)
        self.idir = args_manager['install_dir']

    def install(self):
        eggpath = os.path.join(self.idir, self.eggname)
        if os.path.exists(eggpath):
            logger.info('{0} is already installed', self.packname)
            raise AlreadyInstalled
        logger.info('Installing {0} egg file', self.packname)
        with ZipFile(self.fobj) as z:
            z.extractall(eggpath)
        logger.info('Adding egg file to sys.path')
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
        dist = EggDir(eggpath)
        if args_manager['scripts']:
            for name, content, mode in script_args(dist):
                logger.info('Installing {0} script to {1}', name, BIN)
                target = os.path.join(BIN, name)
                with open(target, 'w' + mode) as f:
                    f.write(content)
                    os.chmod(target, 0755)
        else:
            logger.info('Scripts not installed')
        logger.info('Looking for requirements...')
        try:
            for req in dist.file('requires.txt'):
                self.reqset.add(req)
        except KeyError:
            logger.debug('requires.txt not found')


class Dir(object):
    def __init__(self, path, name, tempdir, reqset=None):
        self.path = path
        self.name = name
        self.tempdir = tempdir
        self.reqset = reqset

    def install(self):
        if self.reqset is not None:
            logger.info('Running setup.py egg_info for {0}', self.name)
            call_setup(self.path, ['egg_info', '--egg-base', self.tempdir])
            try:
                for r in DirTools(os.path.join(self.tempdir, glob(self.tempdir, '*.egg-info')[0])).file('requires.txt'):
                    self.reqset.add(r)
            except (KeyError, ConfigParser.MissingSectionHeaderError):
                logger.debug('requires.txt not found')
        args = []
        if args_manager['install_dir'] != INSTALL_DIR:
            args += ['--install-base', args_manager['install_dir']]
        if not args_manager['scripts']:
            args += ['--install-scripts', self.tempdir]
        if not args_manager['data']:
            args += ['--install-data', self.tempdir]
        run_setup(self.path, self.name, args=args, exc=InstallationError)


class Archive(object):
    def __init__(self, fobj, e, name, reqset):
        self.name = name
        if e == '.zip':
            self.arch = ZipFile(fobj)
        else:
            m = 'r:{0}'.format(e.split('.')[2])

            ## A package should not be a tar file but we don't know
            if e.endswith('.tar'):
                m = 'r'
            self.arch = tarfile.open(fileobj=fobj, mode=m)
        self.reqset = reqset

    def install(self):
        with TempDir() as tempdir:
            self.arch.extractall(tempdir)
            self.arch.close()
            fullpath = os.path.join(tempdir, os.listdir(tempdir)[0])
            Dir(fullpath, self.name, tempdir, self.reqset).install()


class Bundle(object):
    def __init__(self, filepath):
        self.path = os.path.abspath(filepath)

    def install(self):
        with TempDir() as tempdir:
            with ZipFile(self.path) as z:
                z.extractall(tempdir)
            location = os.path.join(tempdir, 'build')
            for f in os.listdir(location):
                logger.info('Installing {0}...', f)
                fullpath = os.path.join(location, f)
                Dir(fullpath, f, tempdir).install()
            logger.info('Bundle installed successfully')


class ArgsManager(object):

    _OPTS = {
            ## Install dependencies?
            'deps': True,
            ## Package Index Url
            'index_url': 'http://pypi.python.org/pypi',
            ## Force installation?
            'upgrade': False,
            ## Install base directory for all installations
            'install_dir': INSTALL_DIR,
            ## Install scripts?
            'scripts': True,
            ## Install data?
            'data': True,
            ## Ask confirmation of uninstall deletions?
            'yes': False,
            ## Use cache when updating?
            'use_cache': True,
            }

    def __getitem__(self, item):
        return ArgsManager._OPTS[item]

    def __setitem__(self, item, v):
        ArgsManager._OPTS[item] = v

args_manager = ArgsManager()
