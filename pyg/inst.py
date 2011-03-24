import re
import os
import sys
import site
import shutil
import zipfile
import ConfigParser
import pkg_resources

from .req import Requirement
from .utils import TempDir, EASY_INSTALL, BIN, File, is_installed
from .types import Archive, Egg, Bundle, ReqSet, InstallationError, AlreadyInstalled
from .log import logger


__all__ = ['Installer', 'Uninstaller']


class Installer(object):
    def __init__(self, req):
        if is_installed(req):
            logger.info('{0} is already installed'.format(req))
            raise AlreadyInstalled
        self.req = req

    @ staticmethod
    def _install_deps(rs):
        logger.info('Installing dependencies...')
        logger.indent += 8
        for req in rs:
            try:
                Installer(req).install()
            except AlreadyInstalled:
                continue
        logger.indent = 0
        logger.info('Finished installing dependencies')

    def install(self):
        r = Requirement(self.req)
        r.install()
        if not r.reqset:
            logger.info('{0} installed successfully'.format(r.name))
            return

        # Now let's install dependencies
        Installer._install_deps(r.reqset)
        logger.info('{0} installed successfully'.format(r.name))

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
        reqset = ReqSet()
        if ext in ('.gz', '.bz2', '.zip'):
            installer = Archive(open(path), ext, packname, reqset)
        elif ext in ('.pybundle', '.pyb'):
            installer = Bundle(filepath)
        elif ext == '.egg':
            installer = Egg(open(path), path, reqset)
        else:
            logger.fatal('E: Cannot install {0}'.format(path))
            sys.exit(1)
        try:
            installer.install()
        except Exception as e:
            logger.fatal('E: {0}'.format(e))
            sys.exit(1)
        Installer._install_deps(reqset)
        logger.info('{0} installed successfully'.format(packname))


class Uninstaller(object):
    def __init__(self, packname):
        self.name = packname

    def uninstall(self):
        uninstall_re = re.compile(r'{0}(-(\d\.?)+(\-py\d\.\d)?\.(egg|egg\-info))?$'.format(self.name), re.I)
        path_re = re.compile(r'\./{0}-[\d\w\.]+-py\d\.\d.egg'.format(self.name), re.I)
        path_re2 = re.compile(r'\.{0}'.format(self.name), re.I)
        dist = pkg_resources.get_distribution(self.name)
        to_del = set()

        if sys.version_info[:2] < (2, 7):
            guesses = [os.path.dirname(dist.location)]
        else:
            guesses = site.getsitepackages() + [site.getusersitepackages()]
        for d in guesses:
            try:
                for file in os.listdir(d):
                    if uninstall_re.match(file):
                        to_del.add(os.path.join(d, file))
            except OSError: ## os.listdir
                continue
        if dist.has_metadata('scripts') and dist.metadata_isdir('scripts'):
            for s in dist.metadata_listdir('scripts'):
                to_del.add(os.path.join(BIN, script))
                if sys.platform == 'win32':
                    to_del.add(os.path.join(BIN, script) + '.bat')
        if dist.has_metadata('entry_points.txt'):
            config = ConfigParser.ConfigParser()
            config.readfp(File(dist.get_metadata_lines('entry_points.txt')))
            if config.has_section('console_scripts'):
                for name, value in config.items('console_scripts'):
                    n = os.path.join(BIN, name)
                    if not os.path.exists(n) and n.startswith('/usr/bin'): ## Searches in the local path
                        n = os.path.join('/usr/local/bin', name)
                    to_del.add(n)
                    if sys.platform == 'win32':
                        to_del.add(n + '.exe')
                        to_del.add(n + '.exe.manifest')
                        to_del.add(n + '-script.py')
        if not to_del:
            logger.warn('Did not find any file to delete')
            sys.exit(1)
        logger.info('Uninstalling {0}'.format(self.name))
        logger.indent += 8
        for d in to_del:
            logger.info(d)
        logger.indent -= 8
        while True:
            u = raw_input('Proceed? (y/[n]) ').lower()
            if u in ('n', ''):
                logger.info('{0} has not been uninstalled'.format(self.name))
                break
            elif u == 'y':
                for d in to_del:
                    try:
                        shutil.rmtree(d)
                    except OSError: ## It is not a directory
                        try:
                            os.remove(d)
                        except OSError:
                            logger.error('E: Cannot delete: {0}'.format(d))
                    logger.info('Deleting: {0}...'.format(d))
                logger.info('Removing egg path from easy_install.pth...')
                with open(EASY_INSTALL) as f:
                    lines = f.readlines()
                with open(EASY_INSTALL, 'w') as f:
                    for line in lines:
                        if path_re.match(line) or path_re2.match(line):
                            continue
                        f.write(line)
                logger.info('{0} uninstalled succesfully'.format(self.name))
                break
