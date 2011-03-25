import os
import sys

import _opts as opts
from .types import InstallationError, AlreadyInstalled


__version__ = '0.1.2'


def _set_up():
    import argparse

    parser = argparse.ArgumentParser(prog='pyg')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    sub = parser.add_subparsers()
    
    sub_inst = sub.add_parser('install')
    sub_inst.add_argument('packname')
    sub_inst.add_argument('-d', '--develop', action='store_true', help='Install the package in development mode')
    sub_inst.add_argument('-r', '--req-file', action='store_true', help='Install packages from the specified requirement file')
    sub_inst.add_argument('-f', '--file', action='store_true', help='Do not download the package but use the local file')
    sub_inst.add_argument('-u', '--upgrade', action='store_true', help='If the package is already installed')
    sub_inst.add_argument('-n', '--no-deps', action='store_true', help='Do not install dependencies')
    sub_inst.add_argument('-i', '--index-url', default='http://pypi.python.org/pypi', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    sub_inst.add_argument('--user', action='store_true', help='Install to user site')
    sub_inst.set_defaults(func=opts.install_func)

    sub_un = sub.add_parser('uninstall')
    sub_un.add_argument('packname', nargs='?')
    sub_un.add_argument('-r', '--req-file', metavar='<path>', help='Uninstall all the packages listed in the given requirement file')
    sub_un.add_argument('-y', '--yes', action='store_true', help='Do not ask confirmation of uninstall deletions')
    sub_un.set_defaults(func=opts.uninst_func)

    sub_rm = sub.add_parser('rm')
    sub_rm.add_argument('packname', nargs='?')
    sub_rm.add_argument('-r', '--req-file', metavar='<path>', help='Uninstall all the packages listed in the given requirement file')
    sub_rm.add_argument('-y', '--yes', action='store_true', help='Do not ask confirmation of uninstall deletions')
    sub_rm.set_defaults(func=opts.uninst_func)
    
    sub_list = sub.add_parser('list')
    sub_list.add_argument('packname')
    sub_list.set_defaults(func=opts.list_func)

    sub_fr = sub.add_parser('freeze')
    sub_fr.add_argument('-c', '--count', action='store_true', help='Only returns requirements count')
    sub_fr.add_argument('-f', '--file', metavar='<path>', help='Writes requirements into the specified file')
    sub_fr.set_defaults(func=opts.freeze_func)

    sub_ln = sub.add_parser('link')
    sub_ln.add_argument('path')
    sub_ln.set_defaults(func=opts.link_func)

    sub_uln = sub.add_parser('unlink')
    sub_uln.add_argument('path', nargs='?')
    sub_uln.add_argument('-a', '--all', action='store_true', help='Remove all links')
    sub_uln.set_defaults(func=opts.unlink_func)

    sub_search = sub.add_parser('search')
    sub_search.add_argument('packname')
    sub_search.set_defaults(func=opts.search_func)

    sub_down = sub.add_parser('download')
    sub_down.add_argument('packname')
    sub_down.add_argument('-d', '--download-dir', default='.', metavar='<path>', help='The destination directory')
    sub_down.add_argument('-p', '--prefer', metavar='<ext>', help='The preferred file type for the download')
    sub_down.set_defaults(func=opts.download_func)
    return parser

def main():
    try:
        parser = _set_up()
        args = parser.parse_args()
        args.func(args)
    except InstallationError:
        sys.exit(1)
    except AlreadyInstalled:
        sys.exit(0)
    sys.exit(0)

if __name__ == '__main__':
    main()