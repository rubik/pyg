import os
import sys
import urllib2

import _opts as opts
from .types import PygError, InstallationError, AlreadyInstalled


__version__ = '0.2'


def _set_up():
    from argh import ArghParser, arg, command

    parser = ArghParser(prog='pyg')
    parser.add_argument('-v', '--version', action='version', version=__version__)


    @ arg('packname')
    @ arg('-r', '--req-file', action='store_true', help='Install packages from the specified requirement file')
    @ arg('-f', '--file', action='store_true', help='Do not download the package but use the local file')
    @ arg('-u', '--upgrade', action='store_true', help='If the package is already installed')
    @ arg('-n', '--no-deps', action='store_true', help='Do not install dependencies')
    @ arg('-i', '--index-url', default='http://pypi.python.org/pypi', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @ arg('-b', '--install-base', metavar='<path>', help='Base installation directory')
    @ arg('--user', action='store_true', help='Install to user site')
    def install(args):
        opts.install_func(args)

    @ arg('packname', nargs='+')
    @ arg('-r', '--req-file', metavar='<path>', help='Uninstall all the packages listed in the given requirement file')
    @ arg('-y', '--yes', action='store_true', help='Do not ask confirmation of uninstall deletions')
    def uninstall(args):
        opts.uninst_func(args)

    @ arg('packname', nargs='+')
    @ arg('-r', '--req-file', metavar='<path>', help='Uninstall all the packages listed in the given requirement file')
    @ arg('-y', '--yes', action='store_true', help='Do not ask confirmation of uninstall deletions')
    def rm(args):
        uninstall(args)

    @ command
    def list(packname):
        opts.list_func(packname)

    @ arg('-c', '--count', action='store_true', help='Only returns requirements count')
    @ arg('-f', '--file', metavar='<path>', help='Writes requirements into the specified file')
    def freeze(args):
        opts.freeze_func(args)

    @ command
    def link(path):
        opts.link_func(path)

    @ arg('path', nargs='?')
    @ arg('-a', '--all', action='store_true', help='Remove all links')
    def unlink(args):
        opts.unlink_func(args)

    @ command
    def search(packname):
        opts.search_func(packname)

    @ command
    def check(packname):
        opts.check_func(packname)

    @ arg('packname')
    @ arg('-u', '--unpack', action='store_true', help='Once downloaded, unpack the package')
    @ arg('-d', '--download-dir', default='.', metavar='<path>', help='The destination directory')
    @ arg('-p', '--prefer', metavar='<ext>', help='The preferred file type for the download')
    def download(args):
        opts.download_func(args)

    parser.add_commands([install, uninstall, rm, list, freeze, link, unlink, list, search, check, download])
    return parser

def main():
    try:
        parser = _set_up()
        args = parser.dispatch()
    except (PygError, InstallationError):
        sys.exit(1)
    except AlreadyInstalled:
        sys.exit(0)
    except urllib2.HTTPError as e:
        sys.exit(e.msg)
    except urllib2.URLError as e:
        sys.exit('urllib error: {0}'.format(e.reason))
    sys.exit(0)

if __name__ == '__main__':
    main()
