import re
import os
import sys
import glob
import shutil
import tarfile
import zipfile
import tempfile
import urlparse
import ConfigParser
import pkg_resources

from pkgtools.pypi import PyPIJson
from pkgtools.pkg import SDist, Develop

from pyg.core import *
from pyg.web import ReqManager, request
from pyg.req import Requirement
from pyg.locations import EASY_INSTALL, USER_SITE, BIN, ALL_SITE_PACKAGES
from pyg.utils import TempDir, File, name, ext, is_installed, is_windows, \
    unpack, call_setup, print_output, installed_distributions
from pyg.log import logger
from pyg.parser.parser import init_parser


__all__ = ['Installer', 'Uninstaller', 'Updater', 'Bundler']


class Installer(object):
    def __init__(self, req):
        self.upgrading = False
        if is_installed(req):
            self.upgrading = True
            if not args_manager['install']['upgrade']:
                    logger.info('{0} is already installed, use -U, --upgrade to upgrade', req)
                    raise AlreadyInstalled
            ## We don't set args_manager['upgrade'] = False
            ## because we want to propagate it to dependencies
            logger.info('{0} is already installed, upgrading...', req)

        self.req = req

    @staticmethod
    def _install_deps(rs, name=None, updater=None):
        if not rs:
            return
        if args_manager['install']['no_deps']:
            logger.info('Skipping dependencies for {0}', name)
            logger.indent = 8
            for req in rs:
                logger.info(req)
            logger.indent = 0
            return
        logger.info('Installing dependencies...')
        dep_error = False
        newly_installed = []
        for req in rs:
            if is_installed(req) and not args_manager['install']['upgrade_all']:
                logger.indent = 8
                logger.info('{0} is already installed, use -A, --upgrade-all to upgrade dependencies', req)
                continue
            logger.indent = 0
            logger.info('Installing {0} (from {1})', req, rs.comes_from)
            logger.indent = 8
            try:
                Installer(req).install()
                newly_installed.append(req)
            except AlreadyInstalled:
                continue
            except InstallationError:
                dep_error = True
                logger.error('Error: {0} has not been installed correctly', req)
                continue
        logger.indent = 0
        if dep_error:
            if updater:
                for req in newly_installed:
                    updater.restore_files(req)
                updater.remove_files(rs.comes_from.name)
                updater.restore_files(rs.comes_from.name)
            logger.error("{0}'s dependencies installation failed", rs.comes_from.name, exc=InstallationError)
        else:
            logger.success('Finished installing dependencies for {0}', rs.comes_from.name)

    def install(self):
        try:
            r = Requirement(self.req)
            updater = Updater(skip=True)
            if self.upgrading:
                updater.remove_files(self.req)
            r.install()

            # Now let's install dependencies
            Installer._install_deps(r.reqset, r.name, updater)
            logger.success('{0} installed successfully', r.name)
        except (KeyboardInterrupt, Exception) as e:
            try:
                msg = e.args[0]
            except IndexError:
                msg = repr(e)

            if isinstance(e, KeyboardInterrupt):
                logger.warn('Process interrupted...')
            else:
                logger.warn('Error: An error occurred during the {0} of {1}: {2}',
                        'upgrading' if self.upgrading else 'installation',
                        self.req,
                        msg)
            if self.upgrading:
                logger.info('Restoring files...')
                updater.restore_files(self.req)
            else:
                logger.info('Removing broken files...')
                Uninstaller(self.req).uninstall()
            logger.error(msg, exc=InstallationError)

    @staticmethod
    def from_req_file(filepath):
        path = os.path.abspath(filepath)
        not_installed = set()
        parser = init_parser()
        with open(path) as f:
            logger.info('{0}:', path)
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    logger.debug('debug: Comment found: {0}', line)
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
                logger.warn(req)
            logger.indent = 0
            raise InstallationError()

    @staticmethod
    def from_file(filepath, packname=None):
        packname = packname or os.path.basename(filepath).split('-')[0]
        reqset = ReqSet(packname)

        e = ext(filepath)
        path = os.path.abspath(filepath)
        if e in ('.tar.gz', '.tar.bz2', '.zip'):
            installer = Archive(open(path), e, packname, reqset)
        elif e in ('.pybundle', '.pyb'):
            installer = Bundle(filepath)
        elif e == '.egg':
            installer = Egg(open(path), path, reqset)
        elif e in ('.exe', '.msi') and is_windows():
            installer = Binary(open(path), e, packname)
        else:
            if tarfile.is_tarfile(path):
                installer = Archive(open(path), None, packname, reqset)
            elif zipfile.is_zipfile(path):
                installer = Archive(open(path), '.zip', packname, reqset)
            else:
                logger.fatal('Error: Cannot install {0}: unknown filetype', packname, exc=InstallationError)
        installer.install()
        Installer._install_deps(reqset, packname)
        logger.success('{0} installed successfully', packname)

    @staticmethod
    def from_dir(path, name=None):
        name = name or os.path.basename(path)
        reqset = ReqSet(name)
        try:
            with TempDir() as tempdir:
                logger.info('Installing {0}', name)
                Dir(path, name, tempdir, reqset).install()
        except Exception as e:
            try:
                msg = e.args[0]
            except IndexError:
                msg = repr(e)
            logger.fatal('Error: {0}: cannot install the package', msg, exc=InstallationError)
        else:
            if reqset:
                Installer._install_deps(reqset)
            logger.success('{0} installed successfully', name)

    @staticmethod
    def from_url(url, packname=None):
        with TempDir() as tempdir:
            packname = packname or urlparse.urlsplit(url).path.split('/')[-1]
            if '#egg=' in url:
                url, packname = url.split('#egg=')
            path = os.path.join(tempdir, packname)
            logger.info('Installing {0} from {1}', packname, url)
            with open(path, 'w') as f:
                f.write(request(url))
            Installer.from_file(path, packname)


class Uninstaller(object):
    def __init__(self, packname, yes=False):
        self.name = packname
        self.yes = yes

    def find_files(self):
        _un_re = re.compile(r'{0}(-(\d\.?)+(\-py\d\.\d)?\.(egg|egg\-info))?$'.format(self.name), re.I)
        _un2_re = re.compile(r'{0}(?:(\.py|\.pyc))'.format(self.name), re.I)
        _un3_re = re.compile(r'{0}.*\.so'.format(self.name), re.I)
        _uninstall_re = [_un_re, _un2_re, _un3_re]

        to_del = set()
        try:
            dist = pkg_resources.get_distribution(self.name)
        except pkg_resources.DistributionNotFound:
            logger.debug('debug: Distribution not found: {0}', self.name)

            ## Create a fake distribution
            ## In Python2.6 we can only use site.USER_SITE
            class FakeDist(object):
                def __init__(self, o):
                    self._orig_o = o
                def __getattr__(self, a):
                    if a == 'location':
                        return USER_SITE
                    elif a == 'egg_name':
                        return (lambda *a: self._orig_o.name + '.egg')
                    return (lambda *a: False)
            dist = FakeDist(self)

        pkg_loc = dist.location

        glob_folder = False

        if pkg_loc in ALL_SITE_PACKAGES:

            # try to detect the real package location
            if dist.has_metadata('top_level.txt'):
                pkg_loc = os.path.join( pkg_loc,
                    dist.get_metadata_lines('top_level.txt').next())
            else:
                glob_folder = True

        # detect egg-info location
        _base_name = dist.egg_name().split('-')
        for n in range(len(_base_name) + 1):
            egg_info_dir = os.path.join(
                dist.location,
                '-'.join(_base_name[:-n if n else None]) + '.egg-info'
            )
            if os.path.exists(egg_info_dir):
                for file in os.listdir(egg_info_dir):
                    if any(u_re.match(file) for u_re in _uninstall_re):
                        to_del.add(os.path.join(egg_info_dir, file))
                to_del.add(egg_info_dir)
                break

        if glob_folder:
            # track individual files inside that folder
            try:
                for file in os.listdir(pkg_loc):
                    if any(u_re.match(file) for u_re in _uninstall_re):
                        to_del.add(os.path.join(pkg_loc, file))
            except OSError:
                logger.debug('debug: OSError when trying to listdir {0}', pkg_loc)
        else: # specific folder (non site-packages)
            if os.path.isdir(pkg_loc):
                to_del.add(pkg_loc)

            # finding package's files into that folder
            if os.path.isdir(pkg_loc):
                for file in os.listdir(pkg_loc):
                    if any(u_re.match(file) for u_re in _uninstall_re):
                        to_del.add(os.path.join(pkg_loc, file))
            else:
                # single file installation
                for ext in '.py .pyc .pyo'.split():
                    _p = pkg_loc + ext
                    if os.path.exists(_p):
                        to_del.add(_p)

        ## Checking for package's scripts...
        if dist.has_metadata('scripts') and dist.metadata_isdir('scripts'):
            for script in dist.metadata_listdir('scripts'):
                to_del.add(os.path.join(BIN, script))

                ## If we are on Windows we have to remove *.bat files too
                if is_windows():
                    to_del.add(os.path.join(BIN, script) + '.bat')

        ## Very important!
        ## We want to remove console scripts too.
        if dist.has_metadata('entry_points.txt'):
            config = ConfigParser.ConfigParser()
            config.readfp(File(dist.get_metadata_lines('entry_points.txt')))
            win32 = sys.platform == 'win32'
            if config.has_section('console_scripts'):
                for name, value in config.items('console_scripts'):
                    n = os.path.join(BIN, name)

                    ## Searches in the local path
                    if not os.path.exists(n) and n.startswith('/usr/bin'):
                        n = os.path.join('/usr/local/bin', name)

                    ## Check existance before adding to `to-del` set.
                    if os.path.exists(n):
                        to_del.add(n)
                    elif win32 and os.path.exists(n + '.exe'):
                        to_del.add(n + '.exe')
                        to_del.add(n + '.exe.manifest')
                        to_del.add(n + '-script.py')
        return to_del

    def uninstall(self):
        path_re = re.compile(r'\./{0}-[\d\w\.]+-py\d\.\d.egg'.format(self.name), re.I)
        path_re2 = re.compile(r'\.{0}'.format(self.name), re.I)
        to_del = self.find_files()
        if not to_del:
            logger.warn('{0}: did not find any files to delete', self.name)
            raise PygError
        logger.info('Uninstalling {0}', self.name)
        logger.indent += 8
        for d in to_del:
            logger.info(d)
        logger.indent -= 8
        do_it = logger.ask('Proceed', bool=('remove files', 'cancel'), dont_ask=self.yes)
        if do_it:
            for d in to_del:
                try:
                    logger.verbose('Deleting: {0}', d)
                    shutil.rmtree(d)
                except OSError: ## It is not a directory
                    try:
                        os.remove(d)
                    except OSError:
                        logger.error('Error: cannot delete {0}', d)
            logger.verbose('Removing egg path from easy_install.pth...')
            with open(EASY_INSTALL) as f:
                lines = f.readlines()
            with open(EASY_INSTALL, 'w') as f:
                for line in lines:
                    if path_re.match(line) or path_re2.match(line):
                        continue
                    f.write(line)
            logger.success('{0} uninstalled succesfully', self.name)
        else:
           logger.info('{0} has not been uninstalled', self.name)


class Updater(object):
    def __init__(self, skip=False):

        ## You should use skip=True when you want to upgrade a single package.
        ## Just do:
        ##>>> u = Updater(skip=True)
        ##>>> u.upgrade(package_name, json, version)
        if not skip:
            logger.debug('Loading list of installed packages... ', addn=False)
            self.working_set = list(installed_distributions())
            logger.info('{0} packages loaded', len(self.working_set))
        self.removed = {}
        self.yes = args_manager['update']['yes']

    def remove_files(self, package):
        uninst = Uninstaller(package, yes=True)
        to_del = uninst.find_files()
        if not to_del:
            logger.info('No files to remove found')
            return

        # XXX: tempfile.mktemp is deprecated, but all other functions create
        # the directory and shutil does not want that.
        tempdir = tempfile.mktemp()
        self.removed[package] = {}
        self.removed[package][tempdir] = []
        for path in to_del:
            self.removed[package][tempdir].append(path)

            # We store files-to-delete into a temporary directory:
            # if something goes wrong during the upgrading we can
            # restore the original files.
            p = os.path.join(tempdir, os.path.basename(path))
            try:
                shutil.copy2(path, p)
            # It is a directory
            except IOError:
                try:
                    shutil.copytree(path, p)
                except OSError:
                    logger.debug('debug: shutil.copytree raised OSError')
                    continue
        logger.enabled = False
        uninst.uninstall()
        logger.enabled = True

    def restore_files(self, package):
        try:
            package = self.removed[package]
        except KeyError:
            logger.debug('debug: `{0}` not found in self.removed', package)
            return
        tempdir = package.keys()[0]
        for path in package[tempdir]:
            p = os.path.join(tempdir, os.path.basename(path))
            try:
                shutil.copy2(p, path)
            ## It is a directory
            except IOError:
                shutil.copytree(p, path)

    def _clean(self):
        logger.debug('debug: Removing temporary directories')
        for package, dirs in self.removed.iteritems():
            try:
                shutil.rmtree(dirs.keys()[0])
            except shutil.Error:
                logger.debug('debug: Error while removing {0}', dirs.keys()[0])
                continue

    def upgrade(self, package_name, json, version):
        '''
        Upgrade a package to the most recent version.
        '''

        logger.info('Removing {0} old version', package_name)
        self.remove_files(package_name)
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
                try:
                    msg = e.args[0]
                except IndexError:
                    msg = repr(e)
                logger.error('Error: An error occurred while installing {0}: {1}', package_name, msg)
                logger.info('Trying another file...')
                logger.indent -= 4
        else:
            logger.warn('Error: Did not find any installable release on PyPI for {0}', package_name)
            try:
                Requirement('{0}=={1}'.format(package_name, version))._install_from_links(args_manager['install']['packages_url'])
            except Exception as e:
                logger.fatal('Error: {0}', e, exc=InstallationError)
                logger.info('Restoring uninstalled files')
                self.restore_files(package_name)
        logger.indent = 0

    def update(self):
        '''
        Searches for updates for every package in the WorkingSet.
        Then calls :meth:`~pyg.inst.Updater.upgrade`.
        '''

        logger.info('Searching for updates')
        for dist in self.working_set:
            package = dist.project_name
            version = Version(dist.version)
            logger.verbose('Found: {0}=={1}', package, version)
            try:
                json = PyPIJson(package).retrieve()
                new_version = Version(json['info']['version'])
            except Exception as e:
                logger.error('Error: Failed to fetch data for {0} ({1})', package, e)
                continue
            if version >= new_version:
                continue

            txt = 'A new release is avaiable for {0}: {1!s} (old {2}), update'.format(package, new_version, dist.version)
            u = logger.ask(txt, bool=('upgrade version', 'keep working version'), dont_ask=self.yes)
            if u:
                self.upgrade(package, json, new_version)
            else:
                logger.info('{0} has not been upgraded', package)
        self._clean()
        logger.success('Updating finished successfully')


class Bundler(object):

    MANIFEST = '''# This is a Pyg bundle file, that contains many source packages
# that can be installed as a group.  You can install this like:
#     pyg install this_file.pyb
# The rest of the file contains a list of all the packages included:
{0}
'''

    def __init__(self, reqs, bundle_name, exclude=[], dest=None, callback=None, use_develop=False):
        self.reqs = reqs
        if not bundle_name.endswith(('.pyb', '.pybundle')):
            bundle_name += '.pyb'
        self.bundle_name = bundle_name
        self.bundled = [] # To keep track of the all bundled packages
        self.exclude = exclude
        self.destination = dest or os.getcwd()
        # callback is a function called after each package is downloaded
        # it should accept two arguments, the requirement and the SDist object.
        self.callback = callback or (lambda *a:a)
        # If this flag is set to True, Pyg will look for local packages before
        # downloading them
        self.use_develop = use_develop

    def _find_develop(self, dir, req):
        try:
            logger.info('Looking for a local package...')
            try:
                dist = Develop(req.name)
            except (ValueError, AttributeError):
                logger.error('Cannot find a local distribution for {0}', req.name, exc=PygError)
            else:
                # XXX: Add a `location` attribute in pkgtools' next release
                location = os.path.abspath(dist._arg_name)
                path = os.path.dirname(location)
                if not req.match(Version(dist.version)):
                    logger.error('Found {0}, but it does not match the requirement', path, exc=PygError)
                setup_py = os.path.join(path, 'setup.py')
                if not os.path.exists(setup_py):
                    logger.error('Cannot find setup.py for {0}', req.name, exc=PygError)
                logger.info('Found a matching package in {0}', path)
                with TempDir() as tempdir:
                    code, output = call_setup(path, ['sdist', '-d', tempdir])
                    if code != 0:
                        logger.fatal('setup.py failed to create the source distribution')
                        print_output(output, 'setup.py sdist')
                        raise PygError
                    arch = glob.glob(os.path.join(tempdir, '*{0}*'.format(req.name)))[0]
                    shutil.move(arch, dir)
                    arch_name = os.path.join(dir, os.path.basename(arch))
                    unpack(arch_name)
                    return arch_name
        except (PygError, IndexError, ValueError):
            return False

    def _download(self, dir, req):
        '''
        Given a destination directory and a requirement to meet, download it and return the archive path.
        '''

        if self.use_develop:
            arch_name = self._find_develop(dir, req)
            if arch_name:
                return arch_name
        manager = ReqManager(req, ('.tar.gz', '.tar.bz2', '.zip'))
        manager.download(dir)
        d_name, version = manager.downloaded_name, manager.downloaded_version
        req.version = version
        arch_name = os.path.join(dir, d_name)
        unpack(arch_name)
        self.bundled.append('{0}=={1}'.format(name(d_name).split('-')[0], version))
        return arch_name

    @staticmethod
    def _clean(dir):
        '''
        Clean the `dir` directory: it removes all top-level files, leaving only sub-directories.
        '''

        logger.debug('debug: bundle: cleaning build dir')
        for file in (d for d in os.listdir(dir) if os.path.isfile(os.path.join(dir, d))):
            logger.debug('debug: Removing: {0}', file)
            os.remove(os.path.join(dir, file))

    def bundle(self, include_manifest=True, build_dir=True, additional_files=[], add_func=None):
        '''
        Create a bundle of the specified package:

            1. Download all required packages (included dependencies)
            2. Clean the build directory
            3. Collect the packages in a single zip file (bundle)
            4. Add the manifest file
            5. Move the bundle from the build dir to the destination
        '''

        def _add_to_archive(zfile, dir):
            for file in os.listdir(dir):
                path = os.path.join(dir, file)
                if os.path.isfile(path):
                    zfile.write(path, os.path.join(dir, file)[len(tempdir):])
                elif os.path.isdir(path):
                    _add_to_archive(zfile, path)

        with TempDir() as tempdir:
            with TempDir() as bundle_dir:
                ## Step 0: we create the `build` directory
                ## If you choose to create a bundle without the build directory,
                ## be aware that your bundle will not be compatible with Pip.
                #####
                if build_dir:
                    build = os.path.join(tempdir, 'build')
                    os.mkdir(build)
                else:
                    build = tempdir
                tmp_bundle = os.path.join(bundle_dir, self.bundle_name)

                ## Step 1: we *recursively* download all required packages
                #####
                reqs = list(self.reqs)
                already_downloaded = set()
                while reqs:
                    r = reqs.pop()
                    if r.name.lower == 'python':
                        continue
                    if any(r.name == rq.name for rq in already_downloaded):
                        logger.debug('debug: Already downloaded: {0}', r)
                        continue
                    if any(r == rq for rq in self.exclude):
                        logger.info('Excluding {0}', r)
                        continue
                    logger.indent = 0
                    logger.info('{0}:', r)
                    logger.indent = 8
                    try:
                        dist = SDist(self._download(build, r))
                        self.callback(r, dist)
                    except ConfigParser.MissingSectionHeaderError:
                        continue
                    try:
                        logger.info('Looking for {0} dependencies', r)
                        logger.indent += 8
                        found = False
                        try:
                            requirements = dist.file('requires.txt')
                        except KeyError:
                            requirements = []
                        for requirement in requirements:
                            rq = Requirement(requirement)
                            if rq not in already_downloaded:
                                logger.info('Found: {0}', requirement)
                                reqs.append(rq)
                                found = True
                        # XXX: Does not work, don't know why!
                        if not found:
                            logger.info('None found')
                    except KeyError:
                        logger.debug('debug: requires.txt not found for {0}', dist)
                    try:
                        as_req = dist.as_req
                    except KeyError:
                        as_req = str(r)
                    already_downloaded.add(Requirement(as_req))
                logger.indent = 0
                logger.success('Finished processing dependencies')

                ## Step 2: we remove all files in the build directory, so we make sure
                ## that when we collect packages we collect only dirs
                #####
                self._clean(build)

                ## Step 3: we collect the downloaded packages and bundle all together
                ## in a single file (zipped)
                #####
                logger.info('Adding packages to the bundle')
                bundle = zipfile.ZipFile(tmp_bundle, mode='w')
                _add_to_archive(bundle, build)

                ## Step 4: add the manifest file
                if include_manifest:
                    logger.info('Adding the manifest file')
                    bundle.writestr('pyg-manifest.txt', Bundler.MANIFEST.format('\n'.join(self.bundled)))

                # Additional files to add
                for path in additional_files:
                    try:
                        _add_to_archive(bundle, path)
                    except (IOError, OSError):
                        logger.debug('debug: Error while adding an additional file: {0}', path)
                if add_func is not None:
                    _add_to_archive(bundle, add_func())
                bundle.close()

                ## Last step: move the bundle to the current working directory
                dest = os.path.join(self.destination, self.bundle_name)
                if os.path.exists(dest):
                    logger.debug('debug: dest already exists, removing it')
                    os.remove(dest)
                shutil.move(tmp_bundle, self.destination)
