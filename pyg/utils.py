import re
import os
import pwd
import sys
import site
import shutil
import zipfile
import tempfile
import subprocess
import collections
import pkg_resources
import glob as glob_mod

from .log import logger

if sys.version_info[:2] < (2, 7):
    USER_SITE = site.USER_SITE
    INSTALL_DIR = None
    try:
        INSTALL_DIR = sorted([p for p in sys.path if p.endswith('dist-packages')],
                            key=lambda i: 'local' in i, reverse=True)[0]
    except IndexError:
        pass
    if not INSTALL_DIR: ## Are we on Windows?
        try:
            INSTALL_DIR = sorted([p for p in sys.path if p.endswith('site-packages')],
                            key=lambda i: 'local' in i, reverse=True)[0]
        except IndexError:
            pass
    if not INSTALL_DIR: ## We have to use /usr/lib/pythonx.y/dist-packages or something similar
        from distutils.sysconfig import get_python_lib
        INSTALL_DIR = get_python_lib()
else:
    INSTALL_DIR = site.getsitepackages()[0]
    USER_SITE = site.getusersitepackages()

EASY_INSTALL = os.path.join(INSTALL_DIR, 'easy-install.pth')
if not os.path.exists(EASY_INSTALL):
    d = os.path.dirname(EASY_INSTALL)
    try:
        if not os.path.exists(d):
            os.makedirs(d)
        open(EASY_INSTALL, 'w').close()
    ## We do not have root permissions...
    except IOError:
        ## So we do not create the file!
        pass

PYG_LINKS = os.path.join(USER_SITE, 'pyg-links.pth')

if sys.platform == 'win32':
    BIN = os.path.join(sys.prefix, 'Scripts')
    if not os.path.exists(BIN):
        BIN = os.path.join(sys.prefix, 'bin')
else:
    BIN = os.path.join(sys.prefix, 'bin')
    ## Forcing to use /usr/local/bin on standard Mac OS X
    if sys.platform[:6] == 'darwin' and sys.prefix[:16] == '/System/Library/':
        BIN = '/usr/local/bin'

def is_installed(req):
    try:
        pkg_resources.get_distribution(req)
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict, ValueError):
        return False
    else:
        return True

def name_from_egg(eggname):
    egg = re.compile(r'([\w\d_]+)-.+')
    return egg.search(eggname).group(1)

def link(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        logger.error('{0} does not exist'.format(path))
    if not os.path.exists(PYG_LINKS):
        open(PYG_LINKS, 'w').close()
    path = os.path.abspath(path)
    logger.info('Linking {0} in {1}...'.format(path, PYG_LINKS))
    if path in open(PYG_LINKS, 'r').read():
        logger.warn('{0} is already linked, exiting now...'.format(path))
    with open(PYG_LINKS, 'a') as f:
        f.write(path)
        f.write('\n')

def unlink(path):
    path = os.path.abspath(path)
    with open(PYG_LINKS) as f:
        lines = f.readlines()
    with open(PYG_LINKS, 'w') as f:
        for line in lines:
            if line.strip() == path:
                logger.info('Removing {0} from {1}...'.format(path, PYG_LINKS))
                continue
            f.write(line)

def call_setup(path, a, stdout=None, stderr=None):
    stdout, stderr = stdout or subprocess.PIPE, stderr or subprocess.PIPE
    code = 'import setuptools;__file__=\'{0}\';execfile(__file__)'.format(os.path.join(path, 'setup.py'))
    args =  [sys.executable, '-c', code]
    cwd = os.getcwd()
    with ChDir(path):
        rcode = subprocess.call(args + a, stdout=stdout, stderr=stderr)
    return rcode

def glob(dir, pattern):
    with ChDir(dir):
        return glob_mod.glob(pattern)

def ext(path):
    p, e = os.path.splitext(path)
    if p.endswith('.tar'):
        return '.tar' + e
    return e


class FileMapper(collections.defaultdict):
    def __missing__(self, key):
        if key in self.pref:
            if key not in self:
                self[key] = self.default_factory()
            return self[key]
        return self.default_factory()


class TempDir(object):
    def __init__(self, prefix='pyg-', suffix='-record'):
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self):
        self.tempdir = tempfile.mkdtemp(self.suffix, self.prefix)
        return self.tempdir
    
    def __exit__(self, *args):
        shutil.rmtree(self.tempdir)


class ChDir(object):
    def __init__(self, dir):
        self.cwd = os.getcwd()
        self.dir = dir

    def __enter__(self):
        os.chdir(self.dir)
        return self.dir

    def __exit__(self, *args):
        os.chdir(self.cwd)


## ZipFile subclass for Python < 2.7
## In Python 2.6 zipfile.ZipFile and tarfile.TarFile do not have __enter__ and
## __exit__ methods
## EDIT: Removed TarFile since it causes problems

class ZipFile(zipfile.ZipFile):
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


## This is a generic file object needed for ConfigParser.ConfigParser
## It implements only a readline() method plus an __iter__ method

class File(object):
    def __init__(self, lines):
        self._i = (l for l in lines)

    def __iter__(self):
        return self._i

    def readline(self):
        try:
            return next(self._i)
        except StopIteration:
            return ''