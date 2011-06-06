import re
import os
import sys
import pkg_resources

from pkgtools.pypi import PyPIXmlRpc

from pyg.vcs import vcs
from pyg.log import logger
from pyg.req import Requirement
from pyg.freeze import freeze, list_releases
from pyg.core import args_manager, PygError, Version
from pyg.inst import Installer, Uninstaller, Updater, Bundler
from pyg.locations import PYG_LINKS, INSTALL_DIR, USER_SITE
from pyg.utils import TempDir, is_installed, link, unlink, unpack
from pyg.web import ReqManager


def check_permissions(dir):
    if not os.path.exists(dir):
        logger.fatal('Error: installation directory {0} does not exist', dir, exc=PygError)
    try:
        path = os.path.join(dir, 'pyg-permissions-test.pth')
        with open(path, 'w'):
            pass
        os.remove(path)
    ## FIXME: Do we need OSError too?
    except (IOError, OSError):
        return False
    else:
        return True

def check_and_exit():
    dir = os.path.abspath(args_manager['install']['install_dir'])
    if not check_permissions(dir):
        sys.exit('''Pyg cannot create new files in the installation directory.
Installation directory was:

    {0}

Perhaps your account does not have write access to this directory?  If the
installation directory is a system-owned directory, you may need to sign in
as the administrator or "root" account.  If you do not have administrative
access to this machine, you may wish to choose a different installation
directory, preferably one that is listed in your PYTHONPATH environment
variable.

If you need further information about Pyg command-line options visit:

    http://pyg.readthedocs.org/en/latest/cmdline.html
or
    http://pyg-installer.co.nr
'''.format(dir))

def _install_package_from_name(package):
    if os.path.exists(package) and not args_manager['install']['ignore']:
        path = os.path.abspath(package)
        logger.info('Installing {0}', path)
        if os.path.isfile(path):
            return Installer.from_file(path)
        elif os.path.isdir(path):
            if not os.path.exists(os.path.join(path, 'setup.py')):
                raise PygError('{0} must contain the setup.py file', path)
            return Installer.from_dir(path)
        else:
            raise PygError('Cannot install the package: {0} is neither a file nor a directory', path)
    if package.startswith(('http://', 'https://')):
        return Installer.from_url(package)
    for s in ('git+', 'hg+', 'bzr+', 'svn+'):
        if package.startswith(s):
            with TempDir() as tempdir:
                return vcs(package, tempdir).install()
    return Installer(package).install()

def install_func(args):
    if args.no_deps:
        args_manager['install']['no_deps'] = True
    if args.upgrade:
        args_manager['install']['upgrade'] = True
    if args.upgrade_all:
        args_manager['install']['upgrade_all'] = True
        args_manager['install']['upgrade'] = True
    if args.no_scripts:
        args_manager['install']['no_scripts'] = True
    if args.no_data:
        args_manager['install']['no_data'] = True
    if args.ignore:
        args_manager['install']['ignore'] = True
    if args.user:
        args_manager['install']['user'] = True
        args_manager['install']['install_dir'] = USER_SITE
    if args.install_dir != INSTALL_DIR:
        dir = os.path.abspath(args.install_dir)
        args_manager['install']['install_dir'] = dir
        if any(os.path.basename(dir) == p for p in args.packname):
            args_manager['install']['ignore'] = True
    args_manager['install']['index_url'] = args.index_url
    check_and_exit()
    if args.editable:
        if len(args.packname) > 1:
            logger.error('Error: Unable to install multiple packages in editable mode')
            return
        package = args.packname[0]
        if os.path.exists(os.path.abspath(package)):
            package = 'dir+{0}#egg={1}'.format(os.path.abspath(package),
                                               os.path.basename(package))
        return vcs(package).develop()
    if args.req_file:
        logger.info('Installing from requirements file')
        for req_file in args.req_file:
            Installer.from_req_file(os.path.abspath(req_file))
        return
    if args.packname:
        for package in args.packname:
            _install_package_from_name(package)

def remove_func(args):
    if args.info:
        for p in args.packname:
            logger.info('{0}:', p)
            files = Uninstaller(p).find_files()
            logger.indent = 8
            for path in files:
                logger.info(path)
            logger.indent = 0
        return
    check_and_exit()
    yes = True if args.yes or args_manager['remove']['yes'] else False
    if len(args.packname) == 1 and args.packname[0] == 'yourself':
        return Uninstaller('pyg', yes).uninstall()
    if args.req_file:
        with open(os.path.abspath(args.req_file)) as f:
            for line in f:
                try:
                    Uninstaller(line.strip(), yes).uninstall()
                except PygError:
                    continue
    for p in args.packname:
        try:
            Uninstaller(p, yes).uninstall()
        except PygError:
            continue

def link_func(path):
    return link(path)

def unlink_func(args):
    if args.all or args_manager['unlink']['all']:
        try:
            os.remove(PYG_LINKS)
        except OSError:
            pass
        return
    return unlink(args.path)

def check_func(name, info=False):
    INFO = '{0.project_name} - {0.version}\nInstalled in {0.location}'
    if not info:
        logger.info(is_installed(name))
        return
    if info:
        try:
            dist = pkg_resources.get_distribution(name)
            logger.info(INFO.format(dist))
        except pkg_resources.DistributionNotFound:
            logger.info(False)

def freeze_func(args):
    f = freeze()
    if args.count or args_manager['freeze']['count']:
        sys.stdout.write(str(len(freeze())) + '\n')
        return
    f = '\n'.join(f) + '\n'
    if args.file or args_manager['freeze']['file']:
        path = args.file or args_manager['freeze']['file']
        with open(os.path.abspath(path), 'w') as req_file:
            req_file.write(f)
    return sys.stdout.write(f)

def list_func(name):
    res = []
    for v, inst in list_releases(name):
        if inst:
            res.append(v + '\tinstalled')
        else:
            res.append(v)
    return sys.stdout.write('\n'.join(res) + '\n')

def search_func(query, exact, show_all_version):
    def _pypi_order(item):
        # this is the old implementation, that looks buggy (try on "sphinx")
        return item['_pypi_ordering']

    def _pkgresources_order(item):
        return (item[0],) +  item[2].v

    res = sorted(PyPIXmlRpc().search({'name': query, 'summary': query}, 'or'))
    processed = {}
    for release in res:
        name, version, summary = release['name'], Version(release['version']), release['summary']

        ## We have already parsed a different version
        if name in processed:
            if show_all_version:
                processed[name].append((version, summary))
            elif version > processed[name][0][0]:
                processed[name] = [(version, summary)]
            continue
        ## This is the first time
        processed[name] = [(version, summary)]

    pattern = re.compile('$|'.join(query) + '$')
    results = []
    for name, values in processed.iteritems():
        try:
            _installed = Version(pkg_resources.get_distribution(name).version)
        except pkg_resources.DistributionNotFound:
            _installed = None
        except Exception:
            logger.warn("WARN: Can't get package data for %r"%name)
            _installed = None
        if exact:
            if pattern.match(name) is None:
                continue

        for version in values:
            if not _installed:
                dec = ''
            elif _installed == version[0]:
                dec = '@'
            else:
                dec = '*'
            results.append((name, dec, version[0], version[1]))

    results = sorted(results, key=_pkgresources_order)
    output = '\n'.join('{0}  {1}{2} - {3}'.format(name, dec, version, summary) for name, dec, version, summary in results)
    return sys.stdout.write(output + '\n')

def download_func(args):
    pref = None
    if args.prefer:
        pref = ['.' + args.prefer.strip('.')]
    name = args.packname
    dest = args_manager['download']['download_dir']
    if args.download_dir != dest:
        dest = args.download_dir
    unpk = args_manager['download']['unpack']
    if args.unpack != unpk:
        unpk = args.unpack
    downloader = ReqManager(Requirement(name), pref)
    downloader.download(dest)
    if downloader.downloaded_name is None:
        logger.fatal('Error: Did not find any files for {0}', name, exc=PygError)
    if unpk:
        path = os.path.abspath(downloader.downloaded_name)
        logger.info('Unpacking {0} to {1}', os.path.basename(path), os.getcwd())
        unpack(path)

def update_func(args):
    if args.yes:
        args_manager['update']['yes'] = True
    check_and_exit()
    up = Updater()
    up.update()

def bundle_func(args):
    def get_reqs(path):
        path = os.path.abspath(path)
        reqs = set()
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                reqs.add(line)
        return reqs
    reqs = []
    if args.req_file:
        reqs = [Requirement(r) for f in args.req_file for r in get_reqs(f)]
    b = Bundler(map(Requirement, args.packages) + reqs, args.bundlename)
    b.bundle()

def shell_func():
    check_and_exit()

    from pyg.parser.shell import PygShell
    PygShell().cmdloop()
