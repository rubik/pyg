import re
import os
import sys
import site
import shutil
import zipfile
import urlparse
import ConfigParser
import pkg_resources

from pkgtools.pypi import PyPIJson
from pkgtools.pkg import WorkingSet, Installed, SDist

from pyg.types import *
from pyg.web import ReqManager
from pyg.req import Requirement
from pyg.locations import EASY_INSTALL, USER_SITE, BIN, PACKAGES_CACHE
from pyg.utils import TempDir, File, name, ext, is_installed, unpack, glob
from pyg.log import logger
from pyg.parser.parser import init_parser


__all__ = ['Installer', 'Uninstaller', 'Updater', 'Bundler']


class Installer(object):
    def __init__(self, req):
        if is_installed(req):
            if not args_manager['install']['upgrade']:
                    logger.info('{0} is already installed', req)
                    raise AlreadyInstalled
            ## We don't set args_manager['upgrade'] = False
            ## because we want to propagate it to dependencies
            logger.info('{0} is already installed, upgrading...', req)

        self.req = req

    @ staticmethod
    def _install_deps(rs, name=None):
        if not rs:
            return
        if args_manager['install']['no_deps']:
            logger.info('Skipping dependencies for {0}', name)
            return
        logger.info('Installing dependencies...')
        for req in rs:
            if is_installed(req):
                logger.info('{0} is already installed', req)
                continue
            logger.indent = 0
            logger.info('Installing {0}', req)
            logger.indent = 8
            try:
                Installer(req).install()
            except AlreadyInstalled:
                continue
            except InstallationError:
                logger.warn('Error: {0} has not been installed correctlry', req)
                continue
        logger.indent = 0
        logger.info('Finished installing dependencies')

    def install(self):
        r = Requirement(self.req)
        try:
            r.install()
        except AlreadyInstalled:
            logger.info('{0} is already installed', r.name)
        except InstallationError as e:
            logger.error(e.args[0], exc=InstallationError)

        # Now let's install dependencies
        Installer._install_deps(r.reqset, r.name)
        logger.info('{0} installed successfully', r.name)

    @ staticmethod
    def from_req_file(filepath):
        path = os.path.abspath(filepath)
        not_installed = set()
        parser = init_parser()
        with open(path) as f:
            logger.info('{0}:', path)
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    logger.debug('Comment found: {0}', line)
                    continue
                try:
                    logger.indent = 8
                    logger.info('Installing: {0}', line)
                    logger.indent = 16
                    parser.dispatch(argv=['install'] + line.split())
                except AlreadyInstalled:
                    continue
                except InstallationError:
                    not_installed.add(line)
                except SystemExit as e:
                    if e.code != 0:
                        logger.warn('W: {0} tried to raise SystemExit: skipping installation')
                    else:
                        logger.info('{0} tried to raise SystemExit, but the exit code was 0')
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

        if is_installed(packname) and not args_manager['install']['upgrade']:
            logger.info('{0} is already installed', packname)
            raise AlreadyInstalled

        if e in ('.tar.gz', '.tar.bz2', '.zip'):
            installer = Archive(open(path), e, packname, reqset)
        elif e in ('.pybundle', '.pyb'):
            installer = Bundle(filepath, reqset)
        elif e == '.egg':
            installer = Egg(open(path), path, reqset)
        else:
            logger.fatal('Error: Cannot install {0}', packname, exc=InstallationError)
        installer.install()
        Installer._install_deps(reqset, packname)
        logger.info('{0} installed successfully', packname)

    @ staticmethod
    def from_dir(path, name=None):
        name = name or os.path.basename(path)
        reqset = ReqSet()
        try:
            with TempDir() as tempdir:
                logger.info('Installing {0}', name)
                Dir(path, name, tempdir, reqset).install()
        except Exception as e:
            logger.fatal('Error: {0}: cannot install the package', e, exc=InstallationError)
        else:
            if reqset:
                Installer._install_deps(reqset)
            logger.info('{0} installed successfully', name)

    @ staticmethod
    def from_url(url, packname=None):
        with TempDir() as t:
            packname = packname if packname is not None else urlparse.urlsplit(url).path.split('/')[-1]
            path = os.path.join(t, packname)
            logger.info('Installing {0}', packname)
            with open(path, 'w') as f:
                f.write(request(url))
            Installer.from_file(path)


class Uninstaller(object):
    def __init__(self, packname, yes=False):
        self.name = packname
        self.yes = yes

    def uninstall(self):
        uninstall_re = re.compile(r'{0}(-(\d\.?)+(\-py\d\.\d)?\.(egg|egg\-info))?$'.format(self.name), re.I)
        uninstall_re2 = re.compile(r'{0}(?:(\.py|\.pyc))'.format(self.name), re.I)
        path_re = re.compile(r'\./{0}-[\d\w\.]+-py\d\.\d.egg'.format(self.name), re.I)
        path_re2 = re.compile(r'\.{0}'.format(self.name), re.I)

        to_del = set()
        try:
            dist = pkg_resources.get_distribution(self.name)
        except pkg_resources.DistributionNotFound:
            logger.debug('debug: dist not found: {0}', self.name)

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
            logger.warn('{0}: did not find any file to delete', self.name)
            raise PygError
        logger.info('Uninstalling {0}', self.name)
        logger.indent += 8
        for d in to_del:
            logger.info(d)
        logger.indent -= 8
        while True:
            if self.yes:
                u = 'y'
            else:
                u = raw_input('Proceed? (y/[n]) ').lower()
            if u in ('n', ''):
                logger.info('{0} has not been uninstalled', self.name)
                break
            elif u == 'y':
                for d in to_del:
                    try:
                        shutil.rmtree(d)
                    except OSError: ## It is not a directory
                        try:
                            os.remove(d)
                        except OSError:
                            logger.error('Error: Cannot delete: {0}', d)
                    logger.info('Deleting: {0}', d)
                logger.info('Removing egg path from easy_install.pth...')
                with open(EASY_INSTALL) as f:
                    lines = f.readlines()
                with open(EASY_INSTALL, 'w') as f:
                    for line in lines:
                        if path_re.match(line) or path_re2.match(line):
                            continue
                        f.write(line)
                logger.info('{0} uninstalled succesfully', self.name)
                break


class Updater(object):
    def __init__(self):
        if not PACKAGES_CACHE or not os.path.exists(PACKAGES_CACHE):
            open(PACKAGES_CACHE, 'w').close()
            logger.info('Cache file not found: $HOME/.pyg/installed_packages.txt')
            self.working_set = list(WorkingSet(onerror=self._pkgutil_onerror, debug=logger.debug))
        else:
            logger.info('Reading cache...')
            with open(PACKAGES_CACHE, 'r') as f:
                self.working_set = []
                for line in f:
                    line = line.strip()
                    package, path = line.split()
                    try:
                        dist = Installed(package)
                    except ValueError:
                        dist = Installed(os.path.basename(path))
                    self.working_set.append((package, (path, dist))
                                            )
        logger.info('{0} packages loaded', len(self.working_set))

    def _pkgutil_onerror(self, pkgname):
        logger.debug('Error while importing {0}', pkgname)

    def upgrade(self, package_name, json, version):
        '''
        Upgrade a package to the most recent version.
        '''

        ## FIXME: Do we have to remove the package old version?
        #logger.info('Removing {0} old version', package_name)
        #logger.indent += 8
        #Uninstaller(package_name, True).uninstall()
        #logger.indent = 0
        args_manager['install']['upgrade'] = True
        logger.info('Upgrading {0} to {1}', package_name, version)
        logger.indent += 8
        for release in json['urls']:
            logger.info('Installing {0}...', release['filename'])
            logger.indent += 4
            try:
                Installer.from_url(release['url'])
                break
            except Exception as e:
                logger.error('Error: An error occurred while installing {0}: {1}', package_name, e)
                logger.info('Trying another file...')
                logger.indent -= 4
        else:
            logger.fatal('Error: Did not find any release on PyPI for {0}', package_name)
        logger.indent = 0

    def update(self):
        '''
        Searches for updates for every package in the WorkingSet.
        Then calls :meth:`~pyg.inst.Updater.upgrade`.
        '''

        logger.info('Searching for updates')
        if PACKAGES_CACHE:
            with open(PACKAGES_CACHE, 'w') as f:
                for package, data in self.working_set:
                    f.write('{0} {1}\n'.format(package, data[0]))
        for package, data in self.working_set:
            path, dist = data
            try:
                json = PyPIJson(package).retrieve()
                new_version = Version(json['info']['version'])
            except Exception as e:
                logger.error('Error: Failed to fetch data for {0}', package, exc=PygError)
            if Version(dist.version) >= new_version:
                continue

            logger.info('A new release is avaiable for {0}: {1!s} (old {2})', package, new_version, dist.version)
            while True:
                if args_manager['update']['yes']:
                    u = 'y'
                else:
                    u = raw_input('Do you want to upgrade? (y/[n]) ').lower()
                if u in ('n', ''):
                    logger.info('{0} has not been upgraded', package)
                    break
                elif u == 'y':
                    self.upgrade(package, json, new_version)
                    break
        logger.info('Updating finished successfully')


class Bundler(object):

    MANIFEST = '''# This is a Pyg bundle file, that contains many source packages
# that can be installed as a group.  You can install this like:
#     pyg install this_file.pyb
# The rest of the file contains a list of all the packages included:
{0}
'''

    def __init__(self, req, bundle_name):
        self.req = req
        if not bundle_name.endswith('.pybundle') and not bundle_name.endswith('.pyb'):
            bundle_name += '.pyb'
        self.bundle_name = bundle_name
        self.bundled = [] # To keep track of the all bundled packages

    def _download(self, dir, req):
        '''
        Given a destination directory and a requirement to meet, download it and return the archive path.
        '''

        manager = ReqManager(req, ('.tar.gz', '.tar.bz2', '.zip'))
        manager.download(dir)
        d_name, version = manager.downloaded_name, manager.downloaded_version
        arch_name = os.path.join(dir, d_name)
        unpack(arch_name)
        self.bundled.append('{0}=={1}'.format(name(d_name).split('-')[0], version))
        return arch_name

    def _clean(self, dir):
        '''
        Clean the `dir` directory: it removes all top-level files, leaving only sub-directories.
        '''

        logger.debug('bundle: cleaning build dir')
        for file in (d for d in os.listdir(dir) if os.path.isfile(os.path.join(dir, d))):
            logger.debug('removing: {0}', file)
            os.remove(os.path.join(dir, file))

    def bundle(self):
        '''
        Create a bundle of the specified package:

            1. Download all required packages (included dependencies)
            2. Clean the build directory
            3. Collect the packages in a single zip file (bundle)
            4. Add the manifest file
            5. Move the bundle from the built dir to the destination
        '''

        def _add_to_archive(zfile, dir):
            for file in os.listdir(dir):
                path = os.path.join(dir, file)
                if os.path.isfile(path):
                    zfile.write(path, os.path.join(dir, file)[len(tempdir):])
                elif os.path.isdir(path):
                    _add_to_archive(zfile, path)

        with TempDir() as tempdir:
            ## Step 1: we create the `build` directory
            #####
            build = os.path.join(tempdir, 'build')
            os.mkdir(build)

            ## Step 2: we recursively download all required packages
            #####
            reqs = [self.req]
            already_downloaded = set()
            while reqs:
                r = reqs.pop()
                logger.indent = 0
                logger.info('{0}:', r)
                logger.indent = 8
                try:
                    dist = SDist(self._download(build, r))
                except ConfigParser.MissingSectionHeaderError:
                    continue
                try:
                    logger.info('Looking for {0} dependencies', r)
                    logger.indent += 8
                    for requirement in dist.file('requires.txt'):
                        if requirement not in already_downloaded:
                            logger.info('Found: {0}', requirement)
                            reqs.append(Requirement(requirement))
                except KeyError:
                    logger.debug('requires.txt not found for {0}', dist)
                try:
                    as_req = dist.as_req()
                except KeyError:
                    as_req = str(r)
                already_downloaded.add(as_req)
            logger.indent = 0
            logger.info('Finished processing dependencies')

            ## Step 3: we remove all files in the build directory, so we make sure
            ## that when we collect packages we collect only dirs
            #####
            self._clean(build)

            ## Step 4: we collect the downloaded packages and bundle all together
            ## in a single file (zipped)
            #####
            logger.info('Adding packages to the bundle')
            bundle = zipfile.ZipFile(os.path.join(tempdir, self.bundle_name), mode='w')
            _add_to_archive(bundle, build)

            ## Step 4: add the manifest file
            logger.info('Adding the manifest file')
            bundle.writestr('pyg-manifest.txt', Bundler.MANIFEST.format('\n'.join(self.bundled)))
            bundle.close()

            ## Last step: move the bundle to the current working directory
            dest = os.path.join(os.getcwd(), self.bundle_name)
            if os.path.exists(dest):
                logger.debug('dest already exists: removing it')
                os.remove(dest)
            shutil.move(os.path.join(tempdir, self.bundle_name), os.getcwd())
