import re
import os
import pwd
import sys
import shutil
import tempfile
import subprocess
import pkg_resources
import glob as glob_mod

from .log import logger

if sys.version_info[:2] < (2, 7):
    import _site._site as site
else:
    import site

## Lame hack entirely for readthedocs.org
if not os.getcwd().startswith('/home/docs/sites/readthedocs.org/checkouts/readthedocs.org/user_builds/pyg/'):
    INSTALL_DIR = site.getsitepackages()[0]
    USER_SITE = site.getusersitepackages()
    EASY_INSTALL = os.path.join(INSTALL_DIR, 'easy-install.pth')
    PYG_LINKS = os.path.join(USER_SITE, 'pyg-links.pth')
    HOME = pwd.getpwnam(os.getlogin()).pw_dir
    PYG_HOME = os.path.join(HOME, '.pyg')
    RECFILE = os.path.join(PYG_HOME, '.pyg-install-record')
else:
    INSTALL_DIR, USER_SITE, EASY_INSTALL, PYG_LINKS, HOME, PYG_HOME, RECFILE = [None] * 7

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
        sys.exit(1)
    if not os.path.exists(PYG_LINKS):
        open(PYG_LINKS, 'w').close()
    path = os.path.abspath(path)
    logger.notify('Linking {0} in {1}...'.format(path, PYG_LINKS))
    if path in open(PYG_LINKS, 'r').read():
        logger.warn('{0} is already linked, exiting now...'.format(path))
        sys.exit(0)
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
                logger.notify('Removing {0} from {1}...'.format(path, PYG_LINKS))
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