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
                logger.debug('Loading options from {0}', cfg)

                ## This is for potential warnings
                logger.indent = 8
                args_manager.load(cfg)
                logger.indent = 0
                break

def init_parser(version=None):
    import sys
    import os
    import _opts as opts
    from pyg.locations import INSTALL_DIR, USER_SITE
    from pyg.parser.formatter import _formatter
    from pyg.core import args_manager
    from argh import ArghParser, arg, command


    parser = ArghParser(prog='pyg')
    parser.add_argument('-d', '--debug', action='store_true', help='Set logger to DEBUG level')
    parser.add_argument('--verbose', action='store_true', help='Set logger to VERBOSE level')
    if version is not None:
        parser.add_argument('-v', '--version', action='version', version=version)
    parser.add_argument('--no-colors', action='store_true', help='Disable colors')


    @arg('packname', nargs='*')
    @arg('-e', '--editable', action='store_true', help='Install a package from an online repository in editable mode')
    @arg('-r', '--req-file', metavar='<path>', action='append', help='Install packages from the specified requirement file')
    @arg('-U', '--upgrade', action='store_true', help='If the package is already installed re-install it again')
    @arg('-A', '--upgrade-all', action='store_true', help='Install again dependencies too')
    @arg('-n', '--no-deps', action='store_true', help='Do not install dependencies')
    @arg('-g', '--ignore', action='store_true', help='Ignore local files or directories')
    @arg('-i', '--index-url', default='http://pypi.python.org/pypi', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @arg('-d', '--install-dir', default=INSTALL_DIR, metavar='<path>', help='Base installation directory')
    @arg('-u', '--user', action='store_true', help='Install to user site')
    @arg('--no-scripts', action='store_true', help='Do not install scripts')
    @arg('--no-data', action='store_true', help='Do not install data files')
    @arg('--force-egg-install', action='store_true', help='Allow installing eggs with a different Python version')
    def install(args):
        '''
        Install a package
        '''

        args_manager['install']['no_deps'] = args.no_deps
        args_manager['install']['upgrade'] = args.upgrade
        args_manager['install']['no_scripts'] = args.no_scripts
        args_manager['install']['no_data'] = args.no_data
        args_manager['install']['ignore'] = args.ignore
        args_manager['install']['force_egg_install'] = args.force_egg_install
        args_manager['install']['index_url'] = args.index_url
        if args.upgrade_all:
            args_manager['install']['upgrade_all'] = True
            args_manager['install']['upgrade'] = True
        if args.user:
            args_manager['install']['user'] = True
            args_manager['install']['install_dir'] = USER_SITE
        if args.install_dir != INSTALL_DIR:
            dir = os.path.abspath(args.install_dir)
            args_manager['install']['install_dir'] = dir
            if any(os.path.basename(dir) == p for p in args.packname):
                ## Automatically set ignore=True when INSTALL_DIR has the same
                ## name of one of the packages to install
                args_manager['install']['ignore'] = True
        opts.install_func(args.packname, args.req_file, args.editable,
                          args_manager['install']['ignore'])

    @arg('packname', nargs='+')
    @arg('-r', '--req-file', metavar='<path>', help='Uninstall all the packages listed in the given requirement file')
    @arg('-y', '--yes', action='store_true', help='Do not ask confirmation of uninstall deletions')
    @arg('-i', '--info', action='store_true', help='Only list files to delete')
    def remove(args):
        '''
        Remove a package
        '''

        args_manager['remove']['yes'] = args.yes
        args_manager['remove']['info'] = args.info
        opts.remove_func(args.packname, args.req_file,
                         args_manager['remove']['yes'], args_manager['remove']['info'])

    @command
    def list(packname):
        '''
        List all versions for a package
        '''

        opts.list_func(packname)

    @arg('-c', '--count', action='store_true', help='Only returns requirements count')
    @arg('-f', '--file', metavar='<path>', help='Writes requirements into the specified file')
    def freeze(args):
        '''
        Freeze current environment (i.e. installed packages)
        '''

        if args.count:
            args_manager['freeze']['count'] = True
        if args.file:
            args_manager['freeze']['file'] = args.file
        opts.freeze_func(args)

    @command
    def link(path):
        '''
        Add a directory to PYTHONPATH
        '''

        opts.link_func(path)

    @arg('path', nargs='?')
    @arg('-a', '--all', action='store_true', help='Remove all links')
    def unlink(args):
        '''
        Remove a previously added directory (with link) from PYTHONPATH
        '''

        if args.all:
            args_manager['unlink']['all'] = True
        opts.unlink_func(args)

    @arg('query', nargs='+')
    @arg('-e', '--exact', action='store_true', help='List only exact hits')
    @arg('-a', '--all', action='store_true', help='Show all versions for specified package')
    def search(args):
        '''
        Search PyPI
        '''

        opts.search_func(args.query, args.exact, args.all)

    @arg('packname')
    @arg('-i', '--info', action='store_true', help='Show infos for specified package')
    def check(args):
        '''
        Check if a package is installed
        '''

        opts.check_func(args.packname, args.info)

    @arg('packname')
    @arg('-u', '--unpack', action='store_true', help='Once downloaded, unpack the package')
    @arg('-d', '--download-dir', default='.', metavar='<path>', help='The destination directory')
    @arg('-p', '--prefer', metavar='<ext>', help='The preferred file type for the download')
    def download(args):
        '''
        Download a package
        '''

        if args.download_dir != args_manager['download']['download_dir']:
            args_manager['download']['download_dir'] = args.download_dir
        if args.prefer != args_manager['download']['prefer']:
            args_manager['download']['prefer'] = args.prefer
        args_manager['download']['unpack'] = args.unpack
        opts.download_func(args)

    @arg('-y', '--yes', action='store_true', help='Do not ask confirmation for the upgrade')
    def update(args):
        '''
        Check for updates for installed packages
        '''

        if args.yes:
            args_manager['update']['yes'] = True
        opts.update_func(args)

    @command
    def shell():
        '''
        Fire up Pyg Shell
        '''

        opts.shell_func()

    @arg('bundlename', help='Name of the bundle to create')
    @arg('packages', nargs='*', help='Name of the package to bundle')
    @arg('-r', '--req-file', action='append', metavar='<path>', help='Requirement files which contains packages to bundle')
    @arg('-e', '--exclude', action='append', metavar='<requirement>', help='Exclude packages matching `requirement`')
    def bundle(args):
        '''
        Create bundles (like Pip's ones)
        '''

        opts.bundle_func(args)

    @command
    def help():
        '''
        Show this help and exit
        '''

        return

    parser.add_commands([install, remove, freeze, link, unlink, list,
                         search, check, download, update, shell, bundle, help])
    parser.formatter_class = _formatter(parser)
    if parser.parse_args(sys.argv[1:]).no_colors:
        args_manager['global']['no_colors'] = True
    return parser
