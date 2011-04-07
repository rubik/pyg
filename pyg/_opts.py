import os
import sys
import urllib2
import urlparse

from .log import logger
from .freeze import freeze
from .req import Requirement
from .types import args_manager, PygError
from .inst import Installer, Uninstaller
from .locations import USER_SITE, PYG_LINKS, INSTALL_DIR
from .utils import is_installed, dirname, link, unlink, unpack, call_setup
from .web import PREFERENCES, PyPI, WebManager, PackageManager, Downloader


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

def install_from_name(name):
    return Installer(name).install()

def install_func(args):
    check_and_exit()
    if args.no_deps:
        args_manager['deps'] = False
    if args.upgrade:
        args_manager['upgrade'] = True
    if args.user:
        args_manager['egg_install_dir'] = USER_SITE
    args_manager['index_url'] = args.index_url
    args_manager['install_base'] = args.install_base
    #if args.develop:
    #    path = os.path.abspath(args.develop)
    #    if args.packname.startswith('http'):
    #        url = args.packname
    #        name = urlparse.urlsplit(url).path.split('/')[-1]
    #        filepath = os.path.join(path, name)
    #        with open(filepath, 'w') as f:
    #            f.write(WebManager.request(url))
    #    else:
    #        d = Downloader(args.packname)
    #        d.download(path)
    #        name = d.name
    #    call_setup()
    if args.file:
        return Installer.from_file(args.packname)
    if args.req_file:
        return Installer.from_req_file(args.packname)
    if args.packname.startswith('http'):
        return Installer.from_url(args.packname)
    return install_from_name(args.packname)

def uninst_func(args):
    check_and_exit()
    if args.yes:
        args_manager['yes'] = True
    if args.req_file:
        with open(os.path.abspath(args.req_file)) as f:
            for line in f:
                try:
                    Uninstaller(line.strip()).uninstall()
                except PygError:
                    continue
    for p in args.packname:
        try:
            Uninstaller(p).uninstall()
        except PygError:
            continue

def link_func(path):
    return link(path)

def unlink_func(args):
    if args.all:
        return os.remove(PYG_LINKS)
    return unlink(args.path)

def check_func(name):
    return sys.stdout.write(str(is_installed(name)) + '\n')

def freeze_func(args):
    f = freeze()
    if args.count:
        sys.stdout.write(str(len(freeze())) + '\n')
        return
    f = '\n'.join(f) + '\n'
    if args.file:
        with open(os.path.abspath(args.file), 'w') as req_file:
            req_file.write(f)
    return sys.stdout.write(f)

def list_func(name):
    res = []
    versions = PyPI().package_releases(name, True)
    if not versions:
        versions = map(str, sorted(WebManager.versions_from_html(name), reverse=True))
    for v in versions:
        if is_installed('{0}=={1}'.format(name, v)):
            res.append(v + '\tinstalled')
        else:
            res.append(v)
    return sys.stdout.write('\n'.join(res) + '\n')

def search_func(name):
    res = PyPI().search({'name': name})
    return sys.stdout.write('\n'.join('{name}  {version} - {summary}'.format(**i) for i in \
                            sorted(res, key=lambda i: i['_pypi_ordering'], reverse=True)) + '\n')

def download_func(args):
    pref = None
    if args.prefer:
        pref = ['.' + args.prefer.strip('.')]
    name = args.packname
    dest = args.download_dir
    unpk = args.unpack
    downloader = Downloader(Requirement(name), pref)
    downloader.download(dest)
    if unpk:
        a = os.path.join(dest, downloader.name)
        logger.info('Unpacking {0} to {1}', downloader.name, dirname(a))
        unpack(a)