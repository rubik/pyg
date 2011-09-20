'''
This module contains the command-line parser. All imports are inside the functions
because we don't want to execute code before the parser is created and when Pyg is
used as a library.
'''

ITERABLE_T = (list, tuple)
COMMANDS = set(['install', 'remove', 'bundle', 'pack', 'download', 'update',
                'search', 'list', 'site', 'check', 'shell', 'completion', 'help'])


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
    #parser.add_argument('-i', '--index-url', default='http://pypi.python.org', metavar="<url>", help='Base URL of Python Package Index (default to %(default)s)')


    @arg('packname', nargs='*')
    @arg('-e', '--editable', action='store_true', help='Install a package from an online repository in editable mode')
    @arg('-r', '--req-file', metavar='<path>', action='append', help='Install packages from the specified requirement file')
    @arg('-U', '--upgrade', action='store_true', help='If the package is already installed re-install it again')
    @arg('-A', '--upgrade-all', action='store_true', help='Like -U, --upgrade, but install again dependencies too')
    @arg('-n', '--no-deps', action='store_true', help='Do not install dependencies')
    @arg('-g', '--ignore', action='store_true', help='Ignore local files or directories')
    @arg('-i', '--index-url', default='http://pypi.python.org', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @arg('-d', '--install-dir', default=INSTALL_DIR, metavar='<path>', help='Base installation directory')
    @arg('-u', '--user', action='store_true', help='Install to user site')
    @arg('--no-scripts', action='store_true', help='Do not install scripts')
    @arg('--no-data', action='store_true', help='Do not install data files')
    @arg('--force-egg-install', action='store_true', help='Allow installing eggs with a different Python version')
    def install(args):
        '''
        Install a package
        '''

        if args.no_deps:
            args_manager['install']['no_deps'] = True
        if args.upgrade:
            args_manager['install']['upgrade'] = True
        if args.no_scripts:
            args_manager['install']['no_scripts'] = True
        if args.no_data:
            args_manager['install']['no_data'] = True
        if args.ignore:
            args_manager['install']['ignore'] = True
        if args.force_egg_install:
            args_manager['install']['force_egg_install'] = True

        if isinstance(args.index_url, ITERABLE_T):
            args.index_url = args.index_url[0]
        args_manager['install']['packages_url'] = args.index_url + '/simple'
        args_manager['install']['index_url'] = args.index_url + '/pypi'

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
    @arg('-l', '--local', action='store_true', help='Add to files to delete local files too.')
    @arg('-i', '--info', action='store_true', help='Only list files to delete')
    def remove(args):
        '''
        Remove a package
        '''

        if args.yes:
            args_manager['remove']['yes'] = True
        if args.info:
            args_manager['remove']['info'] = True
        if args.local:
            args_manager['remove']['local'] = True
        opts.remove_func(args.packname, args.req_file,
                         args_manager['remove']['yes'], args_manager['remove']['info'],
                         args_manager['remove']['local'])

    @arg('packname', nargs=1)
    @arg('-i', '--index-url', nargs=1, default='http://pypi.python.org', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    def list(args):
        '''
        List all versions for a package
        '''

        if isinstance(args.index_url, ITERABLE_T):
            args.index_url = args.index_url[0]

        args_manager['install']['packages_url'] = args.index_url + '/simple'
        args_manager['install']['index_url'] = args.index_url + '/pypi'

        opts.list_func(args.packname[0])

    @arg('-c', '--count', action='store_true', help='Only returns requirements count')
    @arg('-n', '--no-info', action='store_true', help='Do not add site information')
    @arg('-f', '--file', metavar='<path>', help='Writes requirements into the specified file')
    def site(args):
        '''
        Show installed packages and some site information
        '''

        if args.count:
            args_manager['site']['count'] = True
        if args.no_info:
            args_manager['site']['no_info'] = True
        if args.file:
            args_manager['site']['file'] = args.file
        count, no_info, file = args_manager['site']['count'], \
            args_manager['site']['no_info'], args_manager['site']['file']
        opts.site_func(count, no_info, file)

    @arg('query', nargs='+')
    @arg('-i', '--index-url', default='http://pypi.python.org', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @arg('-e', '--exact', action='store_true', help='List only exact hits')
    @arg('-n', '--max-num', type=int, default=None, help='List at most <num> results')
    @arg('-a', '--all', action='store_true', help='Show all versions for specified package')
    def search(args):
        '''
        Search PyPI
        '''

        if isinstance(args.index_url, ITERABLE_T):
            args.index_url = args.index_url[0]

        args_manager['install']['packages_url'] = args.index_url + '/simple'
        args_manager['install']['index_url'] = args.index_url + '/pypi'

        opts.search_func(args.query, args.exact, args.all, args.max_num)

    @arg('packname')
    @arg('-i', '--info', action='store_true', help='Show infos for specified package')
    def check(args):
        '''
        Check if a package is installed
        '''

        opts.check_func(args.packname, args.info)

    @arg('packname')
    @arg('-i', '--index-url', default='http://pypi.python.org', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @arg('-u', '--unpack', action='store_true', help='Once downloaded, unpack the package')
    @arg('-d', '--download-dir', default=os.path.curdir, metavar='<path>', help='The destination directory')
    @arg('-p', '--prefer', metavar='<ext>', help='The preferred file type for the download')
    @arg('-m', '--md5',action='store_true',  help='Show md5 sum & link after download')
    @arg('-n', '--dry',action='store_true',  help='Dry run, just display informations')
    def download(args):
        '''
        Download a package
        '''

        if isinstance(args.index_url, ITERABLE_T):
            args.index_url = args.index_url[0]

        args_manager['install']['packages_url'] = args.index_url + '/simple'
        args_manager['install']['index_url'] = args.index_url + '/pypi'

        if args.download_dir != args_manager['download']['download_dir']:
            args_manager['download']['download_dir'] = args.download_dir
        if args.prefer != args_manager['download']['prefer']:
            args_manager['download']['prefer'] = args.prefer
        args_manager['download']['unpack'] = bool(args.unpack)
        args_manager['download']['md5'] = bool(args.md5)
        if args.dry:
            args_manager['download']['download_dir'] = None
        opts.download_func(args)

    @arg('-i', '--index-url', default='http://pypi.python.org', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @arg('-y', '--yes', action='store_true', help='Do not ask confirmation for the upgrade')
    def update(args):
        '''
        Check for updates for installed packages
        '''

        if isinstance(args.index_url, ITERABLE_T):
            args.index_url = args.index_url[0]

        args_manager['install']['packages_url'] = args.index_url + '/simple'
        args_manager['install']['index_url'] = args.index_url + '/pypi'

        if args.yes:
            args_manager['update']['yes'] = True
        opts.update_func()

    @command
    def shell():
        '''
        Fire up Pyg Shell
        '''

        opts.shell_func()

    @arg('bundlename', help='Name of the bundle to create')
    @arg('packages', nargs='*', help='Name of the package(s) to bundle')
    @arg('-i', '--index-url', default='http://pypi.python.org', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @arg('-r', '--req-file', action='append', metavar='<path>', help='Requirement files which contains packages to bundle')
    @arg('-e', '--exclude', action='append', default=[], metavar='<requirement>', help='Exclude packages matching `requirement`')
    @arg('-d', '--use-develop', action='store_true', help='Look for local packages before downloading them')
    def bundle(args):
        '''
        Create bundles (like Pip's ones)
        '''

        if isinstance(args.index_url, ITERABLE_T):
            args.index_url = args.index_url[0]
        args_manager['install']['packages_url'] = args.index_url + '/simple'
        args_manager['install']['index_url'] = args.index_url + '/pypi'

        if args.exclude:
            args_manager['bundle']['exclude'] = args.exclude
        if args.use_develop:
            args_manager['bundle']['use_develop'] = True
        exclude, use_develop = args_manager['bundle']['exclude'], args_manager['bundle']['use_develop']
        opts.bundle_func(args.packages, args.bundlename, exclude, args.req_file, use_develop)

    @arg('packname', help='Name of the pack to create')
    @arg('package', help='Name of the package to pack')
    @arg('-i', '--index-url', default='http://pypi.python.org', metavar='<url>', help='Base URL of Python Package Index (default to %(default)s)')
    @arg('-d', '--use-develop', action='store_true', help='Look for local packages before downloading them')
    @arg('-e', '--exclude', action='append', default=[], metavar='<requirement>', help='Exclude packages matching `requirement`')
    def pack(args):
        '''
        Create packs
        '''

        if isinstance(args.index_url, ITERABLE_T):
            args.index_url = args.index_url[0]
        args_manager['install']['packages_url'] = args.index_url + '/simple'
        args_manager['install']['index_url'] = args.index_url + '/pypi'

        # XXX: Duplication is evil. (See above.)
        if args.exclude:
            args_manager['pack']['exclude'] = args.exclude
        if args.use_develop:
            args_manager['pack']['use_develop'] = True
        exclude, use_develop = args_manager['pack']['exclude'], args_manager['pack']['use_develop']
        return opts.pack_func(args.package, args.packname, exclude, use_develop)

    @arg('-f', '--file', metavar='<path>', help='Write code for completion into the specified file. Default to %(default)r')
    def completion(args):
        '''
        Generate bash code for Pyg completion
        '''
        return opts.completion_func(COMMANDS, args.file)

    @command
    def help():
        '''
        Show this help and exit
        '''

        return

    parser.add_commands([locals()[cmd] for cmd in COMMANDS])
    parser.formatter_class = _formatter(parser)
    return parser
