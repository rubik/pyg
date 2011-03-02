import sys
import argparse

import pyg.opts as opts


def _set_up():
    parser = argparse.ArgumentParser(prog='pyg', version='0.1')
    parser.add_argument('name')
    sub = parser.add_subparsers()
    
    sub_inst = sub.add_parser('install')
    sub_inst.add_argument('packname')
    sub_inst.add_argument('-d', '--develop', action='store_true')
    sub_inst.set_defaults(func=opts.install_func)
    return parser

def main():
    parser = _set_up()
    if len(sys.argv) == 2:
        sys.exit(opts.install_from_name(sys.argv[1]))
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()