import os
import sys
import glob
import tarfile
import pkg_resources
import ConfigParser
from cStringIO import StringIO

from pkgtools.pkg import Dir as DirTools, EggDir
from pyg.scripts import script_args
from pyg.locations import EASY_INSTALL, INSTALL_DIR, BIN
from pyg.utils import TempDir, ZipFile, call_setup, run_setup, name_from_egg, ext
from pyg.log import logger


__all__ = ['PygError', 'InstallationError', 'AlreadyInstalled', 'Version', 'ReqSet',
           'Egg', 'Archive', 'Dir', 'Bundle', 'Binary', 'args_manager']


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

    def __init__(self, comes_from):
        self._reqs = set()
        self.comes_from = comes_from

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
        self.idir = args_manager['install']['install_dir']

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
        if not args_manager['install']['no_scripts']:
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
                dist = DirTools(glob.glob(os.path.join(self.path, '*egg-info'))[0])
            except (IndexError, ValueError):
                pass
            else:
                try:
                    for r in dist.file('requires.txt'):
                        self.reqset.add(r)
                except (KeyError, ConfigParser.MissingSectionHeaderError):
                    logger.debug('requires.txt not found')
                try:
                    for r in dist.file('dependency_links.txt'):
                        self.reqset.add(r)
                except (KeyError, ConfigParser.MissingSectionHeaderError):
                    logger.debug('dependency_links.txt not found')
        args = []
        if args_manager['install']['install_dir'] != INSTALL_DIR:
            args += ['--prefix', args_manager['install']['install_dir']]
        if args_manager['install']['no_scripts']:
            args += ['--install-scripts', self.tempdir]
        if args_manager['install']['no_data']:
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


class Binary(object):
    def __init__(self, fobj, e, packname):
        self.fobj = fobj
        self.ext = e
        self.name = packname

    def install(self):
        with TempDir() as tempdir:
            filename = 'pyg-installer' + self.ext
            installer = os.path.join(tempdir, filename)
            with open(installer, 'w') as i:
                i.write(self.fobj.getvalue())
            with ChDir(tempdir):
                call_subprocess(['./' + filename])


class ArgsManager(object):

    _OPTS = {
        'install': {
            'upgrade': False,
            'upgrade_all': False,
            'no_deps': False,
            'index_url': 'http://pypi.python.org/pypi',
            'install_dir': INSTALL_DIR,
            'user': False,
            'no_scripts': False,
            'no_data': False,
        },
        'remove': {
            'yes': False
        },
        'freeze': {
            'count': False,
            'file': None
        },
        'unlink': {
            'all': True
        },
        'download': {
            'unpack': False,
            'download_dir': '.',
            'prefer': None
        },
        'update': {
            'yes': False
        },
        'bundle': {
            'exclude': None,
        }
    }

    NOT_BOOL = set(['index_url', 'install_dir', 'file', 'download_dir', 'prefer', 'exclude'])

    def __getitem__(self, item):
        return ArgsManager._OPTS[item]

    def load(self, path):
        cp = ConfigParser.ConfigParser()
        with open(path) as f:
            cp.readfp(f, os.path.basename(path))
        for section in cp.sections():
            if '&' in section:
                sections = [part.strip() for part in section.split('&')]
            else:
                sections = [section]
            for s in sections:
                if s not in self._OPTS:
                    logger.warn('Warning: section does not exist: {0}', section)
                    continue
                for option, value in cp.items(section):
                    option = option.replace('-', '_')
                    if option not in self._OPTS[s]:
                        logger.warn('Warning: option does not exist in section {0}: {1}', option, s)
                        continue
                    if value not in self.NOT_BOOL:
                        value = bool(value)
                    self._OPTS[s][option] = value


args_manager = ArgsManager()
