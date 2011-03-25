import re
import os
import sys
import site
import shutil
import zipfile
import ConfigParser
import pkg_resources

from .req import Requirement
from .utils import TempDir, EASY_INSTALL, USER_SITE, BIN, File, ext, is_installed
from .types import Archive, Egg, Bundle, ReqSet, InstallationError, AlreadyInstalled, args_manager
from .log import logger


__all__ = ['Installer', 'Uninstaller']


class Installer(object):
    def __init__(self, req):
        if is_installed(req):
            if not args_manager['upgrade']:
                logger.info('{0} is already installed'.format(req))
                raise AlreadyInstalled
            else:
                logger.info('{0} is already installed, upgrading...'.format(req))
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
        try:
            r.install()
        except AlreadyInstalled:
            logger.info('{0} is already installed'.format(r.name))
        except InstallationError:
            logger.fatal('E: an error occurred while installing {0}'.format(r.name))
            raise
        if not r.reqset:
            logger.info('{0} installed successfully'.format(r.name))
            return

        # Now let's install dependencies
        if not args_manager['deps']:
            logger.info('Skipping dependencies for {0}'.format(r.name))
            return
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
        e = ext(filepath)
        path = os.path.abspath(filepath)
        packname = os.path.basename(filepath).split('-')[0]
        reqset = ReqSet()

        if is_installed(packname):
            logger.info('{0} is already installed'.format(packname))
            raise AlreadyInstalled

        if e in ('.tar.gz', '.tar.bz2', '.zip'):
            installer = Archive(open(path), e, packname, reqset)
        elif e in ('.pybundle', '.pyb'):
            installer = Bundle(filepath)
        elif e == '.egg':
            installer = Egg(open(path), path, reqset)
        else:
            logger.fatal('E: Cannot install {0}'.format(path))
            raise InstallationError
        try:
            installer.install()
        except Exception as e:
            logger.fatal('E: {0}'.format(e))
            raise InstallationError
        Installer._install_deps(reqset)
        logger.info('{0} installed successfully'.format(packname))


class Uninstaller(object):
    def __init__(self, packname):
        self.name = packname

    def uninstall(self):
        uninstall_re = re.compile(r'{0}(-(\d\.?)+(\-py\d\.\d)?\.(egg|egg\-info))?$'.format(self.name), re.I)
        uninstall_re2 = re.compile(r'{0}(?:(\.py|\.pyc))'.format(self.name), re.I)
        path_re = re.compile(r'\./{0}-[\d\w\.]+-py\d\.\d.egg'.format(self.name), re.I)
        path_re2 = re.compile(r'\.{0}'.format(self.name), re.I)

        to_del = set()
        try:
            dist = pkg_resources.get_distribution(self.name)
        except pkg_resources.DistributionNotFound:
            logger.debug('debug: dist not found: {0}'.format(self.name))

            ## Create a fake distribution
            ## In Python2.6 we can only use site.USER_SITE
            class FakeDist(object):
                def __getattribute__(self, a):
                    if a == 'location':
                        return USER_SITE
                    return (lambda *a: False)
            dist = FakeDist()

        if sys.version_info[:2] < (2, 7):
            guesses = [os.path.dirname(dist.location)]
        else:
            guesses = site.getsitepackages() + [site.getusersitepackages()]
        for d in guesses:
            try:
                for file in os.listdir(d):
                    if uninstall_re.match(file) or uninstall_re2.match(file):
                        to_del.add(os.path.join(d, file))
            ## When os.listdir fails
            except OSError:
                continue

        ## Checking for package's scripts...
        if dist.has_metadata('scripts') and dist.metadata_isdir('scripts'):
            for s in dist.metadata_listdir('scripts'):
                to_del.add(os.path.join(BIN, script))

                ## If we are on Win we have to remove *.bat files too
                if sys.platform == 'win32':
                    to_del.add(os.path.join(BIN, script) + '.bat')

        ## Very important!
        ## We want to remove all files: even console scripts!
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
            if args_manager['yes']:
                u = 'y'
            else:
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
