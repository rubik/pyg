import os
import sys

import _opts as opts
from .types import InstallationError, AlreadyInstalled


__version__ = '0.1'


def _set_up():
    import argparse
    parser = argparse.ArgumentParser(prog='pyg')
    parser.add_argument('-v', '--version', action='version', version=__version__)
    sub = parser.add_subparsers()
    
    sub_inst = sub.add_parser('install')
    sub_inst.add_argument('packname')
    sub_inst.add_argument('-d', '--develop', action='store_true', help='installs the package in development mode')
    sub_inst.add_argument('-r', '--req-file', action='store_true', help='installs packages from the specified requirement file')
    sub_inst.add_argument('-f', '--file', action='store_true', help='does not download the package but use the local file')
    sub_inst.set_defaults(func=opts.install_func)

    sub_un = sub.add_parser('uninstall')
    sub_un.add_argument('packname')
    sub_un.set_defaults(func=opts.uninst_func)

    sub_rm = sub.add_parser('rm')
    sub_rm.add_argument('packname')
    sub_rm.set_defaults(func=opts.uninst_func)
    
    sub_list = sub.add_parser('list')
    sub_list.add_argument('packname')
    sub_list.set_defaults(func=opts.list_func)

    sub_fr = sub.add_parser('freeze')
    sub_fr.add_argument('-c', '--count', action='store_true', help='only returns requirements count')
    sub_fr.add_argument('-f', '--file', metavar='<path>', help='writes requirements into the specified file')
    sub_fr.set_defaults(func=opts.freeze_func)

    sub_ln = sub.add_parser('link')
    sub_ln.add_argument('path')
    sub_ln.set_defaults(func=opts.link_func)

    sub_uln = sub.add_parser('unlink')
    sub_uln.add_argument('path', nargs='?')
    sub_uln.add_argument('-a', '--all', action='store_true', help='remove all links')
    sub_uln.set_defaults(func=opts.unlink_func)

    sub_search = sub.add_parser('search')
    sub_search.add_argument('packname')
    sub_search.set_defaults(func=opts.search_func)
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