import os
import tarfile
import zipfile

from .utils import INSTALL_DIR, TempDir, call_setup
from .log import logger

class Version(object):
    def __init__(self, v):
        self.v = v
        while self.v[-1] == 0:
            self.v = self.v[:-2]

    def __str__(self):
        return self.v

    def __repr__(self):
        return 'Version({0})'.format(self.v)

    def __eq__(self, other):   
        if len(self.v) != len(other.v):
            return False
        return self.v == other.v

    def __ge__(self, other):
        return self.v >= other.v

    def __gt__(self, other):
        return self.v > other.v

    def __le__(self, other):
        return self.v <= other.v

    def __lt__(self, other):
        return self.v < other.v

class Egg(object):
    def __init__(self, fobj, eggname, packname=None):
        self.fobj = fobj
        self.eggname = os.path.basename(eggname)
        self.packname = packname or name_from_egg(eggname)
        self.idir = INSTALL_DIR

    def install(self):
        eggpath = os.path.join(self.idir, self.eggname)
        if os.path.exists(eggpath):
            logger.notify('{0} is already installed'.format(self.packname))
            return
        logger.notify('Installing {0} egg file'.format(self.packname))
        with zipfile.ZipFile(self.fobj) as z:
            z.extractall(os.path.join(self.idir, self.eggname))
        with open(EASY_INSTALL) as f: ## TODO: Fix the opening mode to read and write simultaneously
            lines = f.readlines()
        with open(EASY_INSTALL, 'w') as f:
            f.writelines(lines[:-1])
            f.write('./' + self.eggname + '\n')
            f.write(lines[-1])


class Archive(object):
    def __init__(self, fobj, ext, name):
        self.name = name
        if ext == '.zip':
            self.arch = zipfile.ZipFile(fobj)
        else:
            self.arch = tarfile.open(fileobj=fobj, mode='r:{0}'.format(ext[1:]))

    def install(self):
        with TempDir() as tempdir:
            with self.arch as a:
                a.extractall(tempdir)
            fullpath = os.path.join(tempdir, os.listdir(tempdir)[0])
            logger.notify('Running setup.py for {0}'.format(self.name))
            call_setup(fullpath)