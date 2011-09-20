import os
import glob
import tarfile
import pkg_resources
import ConfigParser

from pkgtools.pkg import Dir as DirTools, EggDir
from pyg.scripts import script_args
from pyg.locations import EASY_INSTALL, INSTALL_DIR, BIN, USER_SITE
from pyg.utils import TempDir, ZipFile, call_subprocess, call_setup, run_setup, \
    name_from_egg, print_output
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


class AlwaysTrue(object):
    def __eq__(self, other): return True
    def __ge__(self, other): return True
    def __gt__(self, other): return True
    def __le__(self, other): return True
    def __lt__(self, other): return True


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
        if v is not None:
            self.v = pkg_resources.parse_version(v)
        else:
            self.v = AlwaysTrue()

    def __str__(self):
        return str(self._v)

    def __repr__(self):
        return 'Version({0})'.format(self._v)

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

    @property
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
        if args_manager['install']['user']:
            self.idir = USER_SITE

    def install(self):
        eggpath = os.path.join(self.idir, self.eggname)
        if os.path.exists(eggpath) and not args_manager['install']['upgrade']:
            logger.info('{0} is already installed', self.packname)
            raise AlreadyInstalled
        logger.info('Installing {0} egg file', self.packname)
        with ZipFile(self.fobj) as z:
            z.extractall(eggpath)
        logger.verbose('Adding egg file to sys.path')
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

        ## Install scripts in the setuptools' way
        if not args_manager['install']['no_scripts']:
            for name, content, mode in script_args(dist):
                logger.info('Installing {0} script to {1}', name, BIN)
                target = os.path.join(BIN, name)
                with open(target, 'w' + mode) as f:
                    f.write(content)
                    os.chmod(target, 0755)
        else:
            logger.info('Scripts not installed')
        logger.info('Looking for dependencies...')
        try:
            for req in dist.requires['install']:
                self.reqset.add(req)
        except KeyError:
            logger.debug('requires.txt not found')


class Dir(object):
    '''
    To install the package this class needs the *path*, a temporary directory's path, and a :class:`ReqSet` object
    to store requirements.
    '''

    def __init__(self, path, name, tempdir, reqset=None):
        self.path = path
        self.name = name
        self.tempdir = tempdir
        self.reqset = reqset

    def install(self):
        '''
        Given a pathname containing a :file:`setup.py` file, install the package.
        First runs `setup.py egg_info` to find out requirements, then runs ``setup.py install``.
        '''

        if self.reqset is not None:
            logger.info('Running setup.py egg_info for {0}', self.name)
            code, output = call_setup(self.path, ['egg_info'])
            if code != 0:
                return print_output(output, 'setup.py egg_info')
            try:
                dist = DirTools(glob.glob(os.path.join(self.path, '*egg-info'))[0])
            except (IndexError, ValueError):
                pass
            else:
                try:
                    for r in dist.requires['install']:
                        self.reqset.add(r)
                except (KeyError, ConfigParser.MissingSectionHeaderError):
                    logger.debug('debug: requires.txt not found')
                #try:
                #    for r in dist.file('dependency_links.txt'):
                #        self.reqset.add(r)
                #except KeyError:
                #    logger.debug('debug: dependency_links.txt not found')
        args = []
        if args_manager['install']['install_dir'] != INSTALL_DIR:
            dir = os.path.abspath(args_manager['install']['install_dir'])
            if not os.path.exists(dir):
                os.makedirs(dir)

            ## Setuptools would not install the package without this hack
            os.putenv('PYTHONPATH', dir)
            args += ['--install-purelib', dir, '--install-platlib', dir]
        if args_manager['install']['no_scripts']:
            args += ['--install-scripts', self.tempdir]
        if args_manager['install']['no_data']:
            args += ['--install-data', self.tempdir]
        if args_manager['install']['user']:
            args += ['--user']
        run_setup(self.path, self.name, args=args, exc=InstallationError)


class Archive(object):
    def __init__(self, fobj, e, name, reqset):
        self.name = name
        if e == '.zip':
            self.arch = ZipFile(fobj)
        else:
            ## A package should not be a tar file but we don't know
            if e is None or e.endswith('.tar'):
                m = 'r'
            else:
                m = 'r:{0}'.format(e.split('.')[2])

            self.arch = tarfile.open(fileobj=fobj, mode=m)
        self.reqset = reqset

    def install(self):
        '''
        Install an archive. First it unpack the archive somewhere and then runs :file:`setup.py`
        '''

        with TempDir() as tempdir:
            self.arch.extractall(tempdir)
            self.arch.close()

            ## This is for archives which have top-level setup.py files
            setup_py = os.path.join(tempdir, 'setup.py')
            if not os.path.exists(setup_py):
                setup_py = glob.glob(os.sep.join([tempdir, '*', 'setup.py']))[0]
            Dir(os.path.dirname(setup_py), self.name, tempdir, self.reqset).install()


class Bundle(object):
    '''
    This class only needs bundle's path. Run :meth:`~pyg.core.Bundle.install` to install packages in it.
    '''

    def __init__(self, filepath):
        self.path = os.path.abspath(filepath)

    def install(self):
        '''
        Install a bundle. For every package runs ``setup.py install``.
        '''

        with TempDir() as tempdir:
            with ZipFile(self.path) as z:
                z.extractall(tempdir)
            location = os.path.join(tempdir, 'build')
            for f in os.listdir(location):
                logger.info('Installing {0}...', f)
                fullpath = os.path.join(location, f)
                Dir(fullpath, f, tempdir).install()
            logger.success('Bundle installed successfully')


class Binary(object):
    def __init__(self, fobj, e, packname):
        self.fobj = fobj
        self.ext = e
        self.name = packname

    def install(self):
        '''
        Install a binary package. Simply run it and hope it works...
        (Still experimental.)
        '''

        with TempDir() as tempdir:
            filename = 'pyg-installer' + self.ext
            installer = os.path.join(tempdir, filename)
            with open(installer, 'w') as i:
                i.write(self.fobj.getvalue())
                call_subprocess(['./' + filename], cwd=tempdir)


class ArgsManager(object):

    _OPTS = {
        'global': {
            'no_colors': False,
        },
        'install': {
            'upgrade': False,
            'upgrade_all': False,
            'no_deps': False,
            'index_url': 'http://pypi.python.org/pypi',
            'packages_url': 'http://pypi.python.org/simple',
            'install_dir': INSTALL_DIR,
            'user': False,
            'no_scripts': False,
            'no_data': False,
            'ignore': False,
            'force_egg_install': False,
        },
        'remove': {
            'yes': False,
            'info': False,
            'local': False,
        },
        'site': {
            'count': False,
            'no_info': False,
            'file': None
        },
        'download': {
            'unpack': False,
            'md5': False,
            'dry': False,
            'download_dir': '.',
            'prefer': None
        },
        'update': {
            'yes': False
        },
        'bundle': {
            'exclude': None,
            'use_develop': False,
        },
        'pack': {
            'dir': '.',
            'exclude': None,
            'use_develop': False
        }
    }

    NOT_BOOL = set(['index_url', 'install_dir', 'file', 'download_dir', 'prefer', 'exclude'])

    def __getitem__(self, item):
        return ArgsManager._OPTS[item]

    @property
    def OPTS(self):
        return self._OPTS

    def load(self, path):
        '''
        Load options from a config file. The syntax is as follows::

            [section_name]
            option=value

        If a option is shared between two or more section you can also write::

            [section1 & section2 & section_n]
            option=value

        Real example::

            [install]
            upgrade_all=True

            [remove]
            yes=True

        The option tree is in the protected variable :attr:`OPTS`.
        '''

        cp = ConfigParser.ConfigParser()
        with open(path) as f:
            cp.readfp(f, os.path.basename(path))
        for section in cp.sections():
            if '&' in section:
                sections = [s.strip() for s in section.split('&')]
            else:
                sections = [section]
            for s in sections:
                if s not in self._OPTS:
                    logger.warn('Warning: section does not exist: {0}', section)
                    continue
                for option, value in cp.items(section):
                    option = option.replace('-', '_')
                    if option not in self._OPTS[s]:
                        logger.warn('Warning: section {0} does not have such option: {1}', s, option)
                        continue
                    if value not in self.NOT_BOOL:
                        if value in ('False', '0', 'false'):
                            value = False
                        else:
                            value = bool(value)
                    if s == 'install' and option == 'upgrade_all':
                        self._OPTS['install']['upgrade'] = True
                    self._OPTS[s][option] = value


args_manager = ArgsManager()
