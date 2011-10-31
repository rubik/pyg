import re
import os
import sys
import copy
import glob
import shutil
import atexit
import tarfile
import zipfile
import urllib2
import urlparse
import functools
import ConfigParser
import pkg_resources
import multiprocessing

from pkgtools.pypi import PyPIJson
from pkgtools.pkg import SDist, Develop, Installed

from pyg.core import *
from pyg.web import ReqManager, request, download
from pyg.req import Requirement
from pyg.locations import EASY_INSTALL, USER_SITE, BIN, BIN2, ALL_SITE_PACKAGES
from pyg.utils import TempDir, ZipFile, File, name, ext, is_installed, is_windows, \
    unpack, call_setup, print_output, installed_distributions
from pyg.log import logger
from pyg.parser.parser import init_parser


__all__ = ['QSIZE', 'Installer', 'Uninstaller', 'Updater', 'Bundler']


# Unfortunately multiprocessing does not allow Values to be inside of a class,
# so we have to keep it global...

# To keep track of the checked packages
QSIZE = multiprocessing.Value('i', 1)


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
            logger.success('Finished installing dependencies for {0}', rs.comes_from)

    def install(self):
        try:
            r = Requirement(self.req)
            updater = FileManager()
            if self.upgrading:
                updater.remove_files(self.req)
            r.install()

            # Now let's install dependencies
            Installer._install_deps(r.reqset, r.name, updater)
            logger.success('{0} installed successfully', r.name)
        except (KeyboardInterrupt, Exception) as e:
            if logger.level == logger.DEBUG:
                raise
            msg = str(e)
            if isinstance(e, KeyboardInterrupt):
                logger.warn('Process interrupted...')
            elif isinstance(e, urllib2.HTTPError):
                logger.error('HTTP Error: {0}', msg[msg.find('HTTP Error') + 11:])
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
        reqset = ReqSet(Requirement(packname))

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
        reqset = ReqSet(Requirement(name))
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
            download(url, 'Downloading {0}'.format(packname), False)
            with open(path, 'w') as f:
                f.write(request(url))
            Installer.from_file(path, packname)


class Uninstaller(object):
    def __init__(self, packname, yes=False, local=False):
        self.name = packname
        self.yes = yes
        self.local = local

    def _old_find_files(self):
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
                try:
                    for file in os.listdir(egg_info_dir):
                        if any(u_re.match(file) for u_re in _uninstall_re):
                            to_del.add(os.path.join(egg_info_dir, file))
                    to_del.add(egg_info_dir)
                # not a directory, like bzr-version.egg-info
                except OSError:
                    logger.debug('debug: not a directory: {0}', egg_info_dir)
                    continue
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

        ## Last check to ensure we don't remove site directories
        for path in copy.copy(to_del):
            if path in ALL_SITE_PACKAGES:
                to_del.remove(path)

        return to_del

    # this decorator filters out local paths
    # added to avoid code duplication into find_files()
    def _filter_locals(meth):
        def wrapper(self):
            to_del = meth(self)
            bin = (BIN,) if BIN2 is None else (BIN, BIN2)
            local = set(path for path in to_del if not path.startswith(tuple(ALL_SITE_PACKAGES) + bin))
            return to_del.difference(local), local
        return wrapper

    @_filter_locals
    def find_files(self):
        try:
            files = Installed(self.name).installed_files()
        except:
            return self._old_find_files()

        to_del = files['lib']
        for name in files['bin']:
            bin = os.path.join(BIN, name)
            if not os.path.exists(bin) and bin.startswith('/usr/bin'):
                bin = os.path.join('/usr/local/bin', name)
            if os.path.exists(bin):
                to_del.add(bin)
            if sys.platform == 'win32' and os.path.exists(bin + '.exe'):
                to_del.add(bin + '.exe')
                to_del.add(bin + '.exe.manifest')
                to_del.add(bin + '-script.py')
        return to_del

    def uninstall(self):
        def sort_paths(p):
            return set(sorted(p, key=lambda i: len(i.split(os.sep)), reverse=True))

        path_re = re.compile(r'\./{0}-[\d\w\.]+-py\d\.\d.egg'.format(self.name), re.I)
        path_re2 = re.compile(r'\.{0}'.format(self.name), re.I)
        to_del, local = map(sort_paths, self.find_files())
        if not to_del:
            if local and not self.local:
                logger.info('Local files (use -l, --local to delete):')
                logger.indent += 8
                for d in local:
                    logger.info(d)
                logger.indent -= 8
                return
            else:
                logger.error('{0}: did not find any files to delete', self.name, exc=PygError)

        logger.info('Uninstalling {0}', self.name)
        logger.indent += 8
        to_del = to_del.union(local if self.local else ())
        for d in to_del:
            logger.info(d)
        if not self.local and local:
            logger.indent -= 8
            logger.info('Local files (use -l, --local to delete):')
            logger.indent += 8
            for d in local:
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
            # remove empty directories
            # FIXME: Is this dangerous?
            #dirs = set(d for d in map(os.path.dirname, to_del) if not os.listdir(d))
            #for d in dirs:
            #    logger.debug('debug: removing {0}', d)
            #    shutil.rmtree(d)
            logger.success('{0} uninstalled succesfully', self.name)
        else:
           logger.info('{0} has not been uninstalled', self.name)


class FileManager(object):

    removed = {}

    def __init__(self):
        self.uninst = functools.partial(Uninstaller, yes=True)

    def remove_files(self, package):
        uninstaller = self.uninst(package)
        to_del = uninstaller.find_files()[0]
        if not to_del:
            logger.info('No files to remove found')
            return

        with TempDir(dont_remove=True) as tempdir:
            self.removed[package] = {}
            self.removed[package][tempdir] = {}
            for i, path in enumerate(to_del):
                self.removed[package][tempdir][i] = path
    
                # We store files-to-delete into a temporary directory:
                # if something goes wrong during the upgrading we can
                # restore the original files.
                base = os.path.join(tempdir, str(i))
                os.mkdir(base)
                p = os.path.join(base, os.path.basename(path))
                if os.path.isdir(path):
                    shutil.copytree(path, p)
                else:
                    shutil.copy2(path, p)
        logger.enabled = False
        uninstaller.uninstall()
        logger.enabled = True

    def restore_files(self, package):
        try:
            package = self.removed[package]
        except KeyError:
            logger.debug('debug: `{0}` not found in self.removed', package)
            return
        tempdir = package.keys()[0]
        for i, path in package[tempdir].iteritems():
            p = os.path.join(tempdir, str(i), os.path.basename(path))
            try:
                shutil.copy2(p, path)
            ## It is a directory
            except (OSError, IOError):
                shutil.copytree(p, path)

    @staticmethod
    @atexit.register
    def _clean():
        logger.debug('debug: Removing temporary directories')
        for package, dirs in FileManager.removed.iteritems():
            logger.debug('debug: {0}', package)
            try:
                shutil.rmtree(dirs.keys()[0])
            except (shutil.Error, OSError):
                logger.debug('debug: Error while removing {0}', dirs.keys()[0])
                continue


class Updater(FileManager):
    def __init__(self):
        logger.info('Loading list of installed packages... ', addn=False)
        self.working_set = list(installed_distributions())
        self.set_len = len(self.working_set)
        logger.info('{0} packages loaded', self.set_len)
        self.yes = args_manager['update']['yes']
        super(Updater, self).__init__()

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
                logger.error('Error: An error occurred while installing {0}: {1}', package_name, e)
                logger.info('Trying another file...')
                logger.indent -= 4
        else:
            logger.warn('Error: Did not find any installable release on PyPI for {0}', package_name)
            try:
                r = Requirement('{0}=={1}'.format(package_name, version))
                r._install_from_links(args_manager['install']['packages_url'])
            except Exception as e:
                logger.fatal('Error: {0}', e, exc=InstallationError)
                logger.info('Restoring uninstalled files')
                self.restore_files(package_name)
        logger.indent = 0

    def check_one(self, args):
        package, version = args
        i = QSIZE.value
        logger.info('\r[{0:.1%} - {1}, {2} / {3}]',
            i / float(self.set_len), package, i, self.set_len, addn=False)
        QSIZE.value += 1
        try:
            json = PyPIJson(package).retrieve()
            new_version = Version(json['info']['version'])
        except Exception as e:
            logger.error('Error: Failed to fetch data for {0} ({1})', package, e)
            return None
        if new_version > version:
            return (package, version, new_version, json)
        return None

    def update(self):
        '''
        Calls :meth:`~pyg.inst.Updater.look_for_updates and the upgrade every package.`
        '''

        logger.info('Searching for updates')
        QSIZE.value = 1
        data = ((dist.project_name, Version(dist.version)) for dist in self.working_set)
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count() + 1)
        packages = pool.map(self.check_one, data)
        pool.close()
        pool.join()
        for data in packages:
            if data is None:
                continue
            package, version, new_version, json = data
            txt = 'A new release is avaiable for {0}: {1!s} (old {2}), update'.format(package,
                                                                                      new_version,
                                                                                      version)
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

    def __init__(self, reqs, bundle_name, exclude=[], callback=None, use_develop=False):
        self.reqs = reqs
        if not bundle_name.endswith(('.pyb', '.pybundle')):
            bundle_name += '.pyb'
        self.bundle_name = bundle_name
        self.bundled = [] # To keep track of the all bundled packages
        self.exclude = exclude
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
                location = os.path.abspath(dist.location)
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

    def _download_all(self, dir):
        reqs = list(self.reqs)
        already_downloaded = set()
        while reqs:
            r = reqs.pop()
            # Hack for virtualenvs
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
            dist = SDist(self._download(dir, r))
            self.callback(r, dist)
            try:
                logger.info('Looking for {0} dependencies', r)
                logger.indent += 8
                found = False
                try:
                    requirements = dist.requires['install']
                except KeyError:
                    requirements = []
                for requirement in requirements:
                    rq = Requirement(requirement)
                    if rq not in already_downloaded:
                        logger.info('Found: {0}', requirement)
                        reqs.append(rq)
                        found = True
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

    @staticmethod
    def _clean(dir):
        '''
        Clean the `dir` directory: it removes all top-level files, leaving only sub-directories.
        '''

        logger.debug('debug: bundle: cleaning build dir')
        for file in (d for d in os.listdir(dir) if os.path.isfile(os.path.join(dir, d))):
            logger.debug('debug: Removing: {0}', file)
            os.remove(os.path.join(dir, file))

    def bundle(self, dest=None, include_manifest=True, build_dir=True, additional_files=[], add_func=None):
        '''
        Create a bundle of the specified package:

            1. Download all required packages (included dependencies)
            2. Clean the build directory
            3. Collect the packages in a single zip file (bundle)
            4. Add the manifest file
            5. Move the bundle from the build dir to the destination
        '''

        destination = dest or os.getcwd()
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
                self._download_all(build)

                ## Step 2: we remove all files in the build directory, so we make sure
                ## that when we collect packages we collect only dirs
                #####
                self._clean(build)

                ## Step 3: we collect the downloaded packages and bundle all together
                ## in a single file (zipped)
                #####
                logger.info('Adding packages to the bundle')
                bundle = ZipFile(tmp_bundle, mode='w')
                bundle.add_to_archive(build, len(tempdir))

                ## Step 4: add the manifest file
                if include_manifest:
                    logger.info('Adding the manifest file')
                    bundle.writestr('pyg-manifest.txt', Bundler.MANIFEST.format('\n'.join(self.bundled)))

                # Additional files to add
                for path in additional_files:
                    try:
                        bundle.add_to_archive(path, len(tempdir))
                    except (IOError, OSError):
                        logger.debug('debug: Error while adding an additional file: {0}', path)
                if add_func is not None:
                    bundle.add_to_archive(add_func(), len(tempdir))
                bundle.close()

                ## Last step: move the bundle to the current working directory
                dest = os.path.join(destination, self.bundle_name)
                if os.path.exists(dest):
                    logger.debug('debug: dest already exists, removing it')
                    os.remove(dest)
                shutil.move(tmp_bundle, destination)
