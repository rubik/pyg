import os
import sys
import urllib2
import urlparse

from pkgtools.pypi import PyPIXmlRpc

from pyg.vcs import vcs
from pyg.log import logger
from pyg.req import Requirement
from pyg.freeze import freeze, list_releases
from pyg.types import args_manager, PygError
from pyg.inst import Installer, Uninstaller, Updater, Bundler
from pyg.locations import USER_SITE, PYG_LINKS, INSTALL_DIR
from pyg.utils import TempDir, is_installed, link, unlink, unpack, call_setup
from pyg.web import ReqManager


def check_permissions():
    try:
        path = os.path.join(INSTALL_DIR, 'pyg-permissions-test.pth')
        with open(path, 'w'):
            pass
        os.remove(path)
    ## FIXME: Do we need OSError too?
    except (IOError, OSError):
        return False
    else:
        return True

def check_and_exit():
    if not check_permissions():
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
'''.format(__import__('pyg').locations.INSTALL_DIR))

def _install_package_from_name(package):
    if os.path.exists(package):
        path = os.path.abspath(package)
        if os.path.isfile(path):
            return Installer.from_file(path)
        elif os.path.isdir(path):
            if not os.path.exists(os.path.join(path, 'setup.py')):
                raise PygError('{0} must contain the setup.py file', path)
            return Installer.from_dir(path)
        else:
            raise PygError('Cannot install that package: {0} is neither a file nor a directory', path)
    if package.startswith('http'):
        return Installer.from_url(package)
    for s in ('git+', 'hg+', 'bzr+', 'svn+'):
        if package.startswith(s):
            with TempDir() as tempdir:
                return vcs(package, tempdir).install()
    return Installer(package).install()

def install_func(args):
    check_and_exit()
    if args.no_deps:
        args_manager['install']['no_deps'] = True
    if args.upgrade:
        args_manager['install']['upgrade'] = True
    if args.no_scripts:
        args_manager['install']['no_scripts'] = True
    if args.no_data:
        args_manager['install']['no_data'] = True
    if args.user:
        args_manager['install']['install_dir'] = USER_SITE
    if args.install_dir != INSTALL_DIR:
        args_manager['install']['install_dir'] = args.install_dir
    args_manager['install']['index_url'] = args.index_url
    if args.editable:
        return vcs(args.packname).develop()
    if args.req_file:
        logger.info('Installing from requirements file')
        for req_file in args.req_file:
            Installer.from_req_file(os.path.abspath(req_file))
        return
    if args.packname:
        for package in args.packname:
            _install_package_from_name(package)

def uninst_func(args):
    check_and_exit()
    yes = True if args.yes or (args_manager['uninstall']['yes'] or args_manager['rm']['yes']) else False
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

def check_func(name):
    return sys.stdout.write(str(is_installed(name)) + '\n')

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

def search_func(name):
    res = PyPIXmlRpc().search({'name': name})
    return sys.stdout.write('\n'.join('{name}  {version} - {summary}'.format(**i) for i in \
                            sorted(res, key=lambda i: i['_pypi_ordering'], reverse=True)) + '\n')

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
    if unpk:
        path = os.path.abspath(downloader.downloaded_name)
        logger.info('Unpacking {0} to {1}', os.path.basename(path), os.getcwd())
        unpack(path)

def update_func(args):
    if args.yes:
        args_manager['update']['yes'] = True
    check_and_exit()
    logger.info('Loading list of installed packages...')
    up = Updater()
    up.update()

def bundle_func(args):
    b = Bundler(Requirement(args.packname), args.bundlename)
    b.bundle()

def shell_func():
    check_and_exit()

    from pyg.parser.shell import PygShell
    PygShell().cmdloop()