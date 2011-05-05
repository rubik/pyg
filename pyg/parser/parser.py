'''
This module contains the command-line parser. All imports are inside the functions
because we don't want to execute code before the parser is created and when Pyg is
used as a library.
'''


def load_options():
    import os.path

    from pyg.core import args_manager
    from pyg.locations import CFG_FILES
    from pyg.log import logger

    if CFG_FILES:
        for cfg in CFG_FILES:
            if os.path.exists(cfg):
                logger.info('Loading options from {0}', cfg)

                ## This is for potential warnings
                logger.indent = 8
                args_manager.load(cfg)
                logger.indent = 0
                break

def init_parser(version=None):
    import _opts as opts
    from pyg.locations import INSTALL_DIR as _loc_install_dir
    from argh import ArghParser, arg, command

    parser = ArghParser(prog='pyg')
    if version is not None:
        parser.add_argument('-v', '--version', action='version', version=version)


    @ arg('packname', nargs='*')
    @ arg('-e', '--editable', action='store_true', help='Install a package from an online repository in editable mode')
    @ arg('-r', '--req-file', metavar='<path>', action='append', help='Install packages from the specified requirement file')
    @ arg('-U', '--upgrade', action='store_true', help='If the package is already installed re-install it again')
    @ arg('-A', '--upgrade-all', action='store_true', help='Install again dependencies too')
    @ arg('-n', '--no-deps', action='store_true', help='Do not install dependencies')
    @ arg('-i', '--index-url', default='http://pypi.python.org/pypi', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @ arg('-d', '--install-dir', default=_loc_install_dir, metavar='<path>', help='Base installation directory')
    @ arg('-u', '--user', action='store_true', help='Install to user site')
    @ arg('--no-scripts', action='store_true', help='Do not install scripts')
    @ arg('--no-data', action='store_true', help='Do not install data files')
    def install(args):
        opts.install_func(args)

    @ arg('packname', nargs='+')
    @ arg('-r', '--req-file', metavar='<path>', help='Uninstall all the packages listed in the given requirement file')
    @ arg('-y', '--yes', action='store_true', help='Do not ask confirmation of uninstall deletions')
    def remove(args):
        opts.remove_func(args)

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

    @ arg('-y', '--yes', action='store_true', help='Do not ask confirmation for the upgrade')
    def update(args):
        opts.update_func(args)

    @ command
    def shell():
        opts.shell_func()

    @ arg('bundlename', help='Name of the bundle to create')
    @ arg('packages', nargs='*', help='Name of the package to bundle')
    @ arg('-r', '--req-file', action='append', metavar='<path>', help='Requirement files which contains packages to bundle')
    @ arg('-e', '--exclude', action='append', metavar='<requirement>', help='Exclude packages matching `requirement`')
    def bundle(args):
        opts.bundle_func(args)

    parser.add_commands([install, remove, freeze, link, unlink, list,
                         search, check, download, update, shell, bundle])
    return parser