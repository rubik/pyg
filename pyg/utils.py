import re
import os
import pwd
import sys
import site
import shutil
import tempfile
import subprocess
import pkg_resources

from .log import logger


INSTALL_DIR = site.getsitepackages()[0]
USER_SITE = site.getusersitepackages()
EASY_INSTALL = os.path.join(INSTALL_DIR, 'easy-install.pth')
PYG_LINKS = os.path.join(USER_SITE, 'pyg-links.pth')
HOME = pwd.getpwnam(os.getlogin()).pw_dir
PYG_HOME = os.path.join(HOME, '.pyg')
RECFILE = os.path.join(PYG_HOME, '.pyg-install-record')

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
            if line[:-1] == path:
                logger.notify('Removing {0} from {1}...'.format(path, PYG_LINKS))
                continue
            f.write(line)

def call_setup(path):
    code = '__file__=\'{0}\';execfile(__file__)'.format(os.path.join(path, 'setup.py'))
    args =  ['python', '-c', code, 'install', 'egg_info', '--egg-base', PYG_HOME]
    cwd = os.getcwd()
    os.chdir(path)
    subprocess.call(args, stdout=subprocess.PIPE)
    os.chdir(cwd)


class TempDir(object):
    def __init__(self, prefix='pyg-', suffix='-record'):
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self):
        self.tempdir = tempfile.mkdtemp(self.suffix, self.prefix)
        return self.tempdir
    
    def __exit__(self, *args):
        shutil.rmtree(self.tempdir)