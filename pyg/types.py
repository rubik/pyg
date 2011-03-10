import os

from .utils import INSTALL_DIR


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
            return 0
        logger.notify('Installing {0} egg file'.format(self.packname))
        with zipfile.ZipFile(self.fobj) as z:
            z.extractall(os.path.join(self.idir, self.eggname))
        with open(EASY_INSTALL) as f: ## TODO: Fix the opening mode to read and write simultaneously
            lines = f.readlines()
        with open(EASY_INSTALL, 'w') as f:
            f.writelines(lines[:-1])
            f.write('./' + self.eggname + '\n')
            f.write(lines[-1])