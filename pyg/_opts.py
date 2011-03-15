import os
import sys
from .web import PyPI, WebManager
from .inst import Installer, Uninstaller
from .utils import USER_SITE, PYG_LINKS, is_installed, link, unlink
from .freeze import freeze


def install_from_name(name):
    return Installer(name).install()

def install_func(args):
    if args.develop:
        raise NotImplementedError('not implemented yet')
    if args.file:
        return Installer.from_file(args.packname)
    if args.req_file:
        return Installer.from_req_file(args.packname)
    return install_from_name(args.packname)

def uninst_func(args):
    return Uninstaller(args.packname).uninstall()

def link_func(args):
    return link(args.path)

def unlink_func(args):
    if args.all:
        return os.remove(pyg_links())
    return unlink(args.path)

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

def list_func(args):
    res = []
    name = args.packname
    versions = PyPI().package_releases(name, True)
    if not versions:
        versions = map(str, sorted(WebManager.versions_from_html(name), reverse=True))
    for v in versions:
        if is_installed('{0}=={1}'.format(name, v)):
            res.append(v + '\tinstalled')
        else:
            res.append(v)
    return sys.stdout.write('\n'.join(res) + '\n')

def search_func(args):
    res = PyPI().search({'name': args.packname})
    return sys.stdout.write('\n'.join('{name}  {version} - {summary}'.format(**i) for i in \
                            sorted(res, key=lambda i: i['_pypi_ordering'], reverse=True)) + '\n')