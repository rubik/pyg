import os
import pwd
import sys
import site
import shutil
import tempfile
import pkg_resources

from .log import logger


def sitep():
    return site.getusersitepackages()

def pyg_links():
    return os.path.join(sitep(), 'pyg-links.pth')

def is_installed(req):
    try:
        pkg_resources.get_distribution(req)
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict, ValueError):
        return False
    else:
        return True

def home():
    return pwd.getpwnam(os.getlogin()).pw_dir

def link(path):
    sitepath = pyg_links()
    if not os.path.exists(sitepath):
        open(sitepath, 'w').close()
    path = os.path.abspath(path)
    logger.notify('Linking {0} in {1}...'.format(path, sitepath))
    if path in open(sitepath, 'r').read():
        logger.warn('{0} is already linked, exiting now...'.format(path))
        sys.exit(0)
    with open(sitepath, 'a') as f:
        f.write(path)
        f.write('\n')

def unlink(path):
    path = os.path.abspath(path)
    with open(pyg_links()) as f:
        lines = f.readlines()
    with open(pyg_links(), 'w') as f:
        for line in lines:
            if line[:-1] == path:
                logger.notify('Removing {0} from {1}...'.format(path, pyg_links()))
                continue
            f.write(line)


class TempDir(object):
    def __init__(self, prefix='pyg-', suffix='-record'):
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self):
        self.tempdir = tempfile.mkdtemp(self.suffix, self.prefix)
        return self.tempdir
    
    def __exit__(self, *args):
        shutil.rmtree(self.tempdir)