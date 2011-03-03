import sys
from .web import PyPI, WebManager
from .inst import Installer
from .utils import is_installed


def install_from_name(name):
    return Installer(name).install()

def install_func(args):
    if args.develop:
        raise NotImplementedError('not implemented yet')
    if args.file:
        return Installer.from_file(args.file)
    if args.bundle:
        return Installer.from_bundle(args.bundle)
    return install_from_name(args.packname)

def list_func(args):
    res = []
    name = args.packname
    versions = PyPI().package_releases(name, True)
    if not versions:
        versions = map(str, sorted(WebManager.versions_from_html(name), reverse=True))
    for v in versions:
        if is_installed(name, v):
            res.append(v + '\tinstalled')
        else:
            res.append(v)
    return sys.stdout.write('\n'.join(res) + '\n')