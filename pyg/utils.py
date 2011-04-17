import re
import os
import pwd
import sys
import shutil
import zipfile
import tarfile
import tempfile
import subprocess
import collections
import pkg_resources
import glob as glob_mod


from pyg.locations import PYG_LINKS
from pyg.log import logger


PYTHON_VERSION = '.'.join(map(str, sys.version_info[:2]))

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

def right_egg(eggname):
    vcode = 'py{0}'.format('.'.join(map(str, sys.version_info[:2])))
    return vcode in eggname

def version_egg(eggname):
    eggv = re.compile(r'py(\d\.\d)')
    return eggv.search(eggname).group(1)

def link(path):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        logger.error('{0} does not exist', path)
    if not os.path.exists(PYG_LINKS):
        if not os.path.exists(os.path.dirname(PYG_LINKS)):
            os.makedirs(os.path.dirname(PYG_LINKS))
        open(PYG_LINKS, 'w').close()
    path = os.path.abspath(path)
    logger.info('Linking {0} in {1}...', path, PYG_LINKS)
    if path in open(PYG_LINKS, 'r').read():
        logger.warn('{0} is already linked, exiting now...', path)
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
                logger.info('Removing {0} from {1}...', path, PYG_LINKS)
                continue
            f.write(line)

def call_subprocess(args, stdout, stderr):
    try:
        return subprocess.check_call(args, stdout=stdout, stderr=stderr)
    except subprocess.CalledProcessError as e:
        return e.returncode

def call_setup(path, a):
    code = 'import setuptools;__file__=\'{0}\';execfile(__file__)'.format(os.path.join(path, 'setup.py'))
    args =  [sys.executable, '-c', code]
    with ChDir(path):
        stdout = open('pyg-proc-stdout', 'w')
        stderr = open('pyg-proc-stderr', 'w')
        return call_subprocess(args + a, stdout=stdout, stderr=stderr)

def run_setup(path, name, global_args=[], args=[], exc=TypeError):
    logger.info('Running setup.py install for {0}', name)
    if call_setup(path, global_args + ['install', '--single-version-externally-managed',
                                       '--record', '.pyg-install-record'] + args):
        logger.fatal('setup.py did not install {0}', name, exc=exc)

def glob(dir, pattern):
    with ChDir(dir):
        return glob_mod.glob(pattern)

def dir_ext(path):
    p, e = os.path.splitext(path)
    if p.endswith('.tar'):
        e = '.tar' + e
        p = p[:-4]
    return p, e

def dirname(path):
    return dir_ext(path)[0]

def ext(path):
    return dir_ext(path)[1]

def unpack(path):
    path = os.path.abspath(path)
    d, e = dir_ext(path)
    if e in ('.egg', '.zip'):
        arch = ZipFile(path)
    elif e in ('.tar', '.tar.gz', '.tar.bz2'):
        mode = 'r' if e == '.tar' else 'r:' + e.split('.')[2]
        arch = tarfile.open(path, mode=mode)
    arch.extractall(d)


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

#class TarFile(tarfile.TarFile):
#    def __enter__(self):
#        return self
#
#    def __exit__(self, type, value, traceback):
#        self.close()


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
