import re
import os
import sys
import site
import shutil
import zipfile
import pkg_resources

from .req import Requirement
from .utils import TempDir, EASY_INSTALL, is_installed
from .types import Archive, Egg, Bundle, InstallationError, AlreadyInstalled
from .log import logger


__all__ = ['Installer', 'Uninstaller']


class Installer(object):
    def __init__(self, req):
        if is_installed(req):
            logger.notify('{0} is already installed, exiting now...'.format(req))
            raise AlreadyInstalled
        self.req = req

    def _install_hook(self, req):
        _name_re = re.compile(r'^([^\(]+)')
        print _name_re.search(str(req)).group().strip().split()
        r = Requirement(_name_re.search(str(req)).group().strip().split())
        Installer('{0}=={1}'.format(r.name, r.version)).install()

    def install(self):
        r = Requirement(self.req)
        r.install()

        # Now let's install dependencies
        if r.op:
            req = pkg_resources.Requirement.parse(str(r))
        else:
            req = pkg_resources.Requirement.parse('{0}=={1}'.format(r, str(r.version)))
        try:
            pkg_resources.WorkingSet().resolve((req,),
                                                installer=self._install_hook)
        except pkg_resources.VersionConflict as e:
            print e.message
            logger.warn('W: Version conflict: {0}'.format(r))

    @ staticmethod
    def from_req_file(filepath):
        path = os.path.abspath(filepath)
        not_installed = set()
        with open(path) as f:
            for line in f:
                try:
                    Installer(line.strip()).install()
                except AlreadyInstalled:
                    continue
                except InstallationError:
                    not_installed.add(line.strip())
        if not_installed:
            logger.warn('These packages have not been installed:')
            logger.indent = 8
            for req in not_installed:
                logger.info(req)
            logger.indent = 0
            raise InstallationError

    @ staticmethod
    def from_file(filepath):
        ext = os.path.splitext(filepath)[1]
        path = os.path.abspath(filepath)
        packname = os.path.basename(filepath).split('-')[0]
        if ext in ('.gz', '.bz2', '.zip'):
            installer = Archive(open(path), ext, packname)
        elif ext in ('.pybundle', '.pyb'):
            installer = Bundle(filepath)
        elif ext == '.egg':
            installer = Egg(open(path), path)
        else:
            logger.fatal('E: Cannot install {0}'.format(path))
            sys.exit(1)
        try:
            installer.install()
        except Exception as e:
            logger.fatal('E: {0}'.format(e))
            sys.exit(1)


class Uninstaller(object):
    def __init__(self, packname):
        self.name = packname

    def uninstall(self):
        uninstall_re = re.compile(r'{0}(-(\d\.?)+(\-py\d\.\d)?\.(egg|egg\-info))?'.format(self.name), re.I)
        path_re = re.compile('./{0}-[\d\w\.]+-py\d\.\d.egg'.format(self.name))
        guesses = site.getsitepackages() + [site.getusersitepackages()]
        to_del = []
        for d in guesses:
            try:
                for file in os.listdir(d):
                    if uninstall_re.match(file):
                        to_del.append(os.path.join(d, file))
            except OSError: ## os.listdir
                continue
        if not to_del:
            logger.warn('Did not find any file to delete')
            sys.exit(1)
        logger.notify('Uninstalling {0}'.format(self.name))
        logger.indent += 8
        for d in to_del:
            logger.info(d)
        logger.indent -= 8
        while True:
            u = raw_input('Proceed? (y/[n]) ').lower()
            if u in ('n', ''):
                logger.info('{0} has not been uninstalled'.format(self.name))
                sys.exit(0)
            elif u == 'y':
                for d in to_del:
                    try:
                        shutil.rmtree(d)
                    except OSError: ## It is not a directory
                        os.remove(d)
                    logger.notify('Deleting: {0}...'.format(d))
                logger.notify('Removing egg path from easy_install.pth...')
                with open(EASY_INSTALL) as f:
                    lines = f.readlines()
                with open(EASY_INSTALL, 'w') as f:
                    for line in lines:
                        if not path_re.match(line):
                            f.write(line)
                logger.notify('{0} uninstalled succesfully'.format(self.name))
                sys.exit(0)
