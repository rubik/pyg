import os
import sys
import argparse

import _opts as opts


__version__ = '0.1'

pyg_home = os.path.join(os.environ['HOME'], '.pyg')
if not os.path.exists(pyg_home):
    os.makedirs(pyg_home)

def _set_up():
    parser = argparse.ArgumentParser(prog='pyg', version='0.1')
    sub = parser.add_subparsers()
    
    sub_inst = sub.add_parser('install')
    sub_inst.add_argument('packname')
    sub_inst.add_argument('-d', '--develop', action='store_true', help='Installs the package in development mode')
    sub_inst.add_argument('-b', '--bundle', metavar='PATH', help='Installs the packages in the bundle file')
    sub_inst.add_argument('-f', '--file', metavar='PATH', help='Does not download the package but use the file in `PATH`')
    sub_inst.set_defaults(func=opts.install_func)

    sub_un = sub.add_parser('uninstall')
    sub_un.add_argument('packname')
    sub_un.set_defaults(func=opts.uninst_func)
    
    sub_list = sub.add_parser('list')
    sub_list.add_argument('packname')
    sub_list.set_defaults(func=opts.list_func)

    sub_search = sub.add_parser('search')
    sub_search.add_argument('packname')
    return parser

def main():
    parser = _set_up()
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()