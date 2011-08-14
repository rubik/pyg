__version__ = '0.8a'


def _suggest_cmd(argv):
    import difflib
    from pyg.log import logger
    from pyg.parser.parser import COMMANDS

    if not argv:
        argv.append('--help')
        return
    cmd = argv[0]
    _proposals = [c for c in COMMANDS if c.startswith(cmd)]
    if len(_proposals) == 1:
        argv[0] = _proposals[0]
    elif len(_proposals):
        logger.exit('Ambiguous command, {0!r} could be one of:\n\t{1}'.format(cmd,
                                                                            '\n\t'.join(_proposals))
                    )
    else:
        close = '\n\t'.join(difflib.get_close_matches(cmd, COMMANDS, cutoff=0.3))
        logger.exit('{0!r} is not a Pyg command.\n\nDid you mean one of these?\n\t{1}'.format(cmd, close))

def _clean_argv(argv):
    from pyg.log import logger

    precmd = argv[:2]
    if '-d' in precmd or '--debug' in precmd:
        logger.level = logger.DEBUG
        try:
            argv.remove('-d')
        except ValueError:
            argv.remove('--debug')
    elif '--verbose' in precmd:
        logger.level = logger.VERBOSE
        argv.remove('--verbose')


def main(argv=None):
    import sys
    import urllib2

    try:
        ## If Python fails to import pyg we just add this directory to
        ## sys.path so we don't have to worry whether Pyg is installed or not.
        __import__('pyg')
    except ImportError:
        sys.path.insert(0, '..')
    from pyg.parser.parser import init_parser, load_options
    from pyg.core import PygError, InstallationError, AlreadyInstalled, args_manager
    from pyg.log import logger

    try:
        # Output Pyg version when `-v, --version` is specified
        if len(sys.argv) == 2 and sys.argv[-1] in ('-v', '--version'):
            logger.info(__version__)
            sys.exit(0)
        parser = init_parser(__version__)
        argv = argv or sys.argv[1:]
        # we have to remove -d, --debug and --verbose to make
        # _suggest_cmd work
        _clean_argv(argv)
        _suggest_cmd(argv)
        args = parser.parse_args(argv)
        load_options()
        if args.no_colors or args_manager['global']['no_colors']:
            logger.disable_colors()
        parser.dispatch(argv=argv)
    except (PygError, InstallationError, ValueError) as e:
        sys.exit(1)
    except AlreadyInstalled:
        sys.exit(0)
    except urllib2.HTTPError as e:
        logger.exit('HTTPError: {0}'.format(e.msg))
    except urllib2.URLError as e:
        logger.exit('urllib error: {0}'.format(e.reason if hasattr(e, 'reason') else e.msg))
    except KeyboardInterrupt:
        logger.exit('Process interrupted...')
    except Exception as e:
        if logger.level == logger.DEBUG:
            raise
        logger.exit('Unknown error occurred: {0}'.format(e))

    sys.exit(0)

if __name__ == '__main__':
    main()
