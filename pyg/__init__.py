__version__ = '0.8a'


def main(argv=None):
    import sys
    import urllib2

    try:
        ## If Python fails to import pyg we just add this directory to
        ## sys.path so we don't have to worry whether Pyg is installed or not.
        __import__('pyg')
    except ImportError:
        sys.path.insert(0, '..')
    from pyg.parser.parser import init_parser, load_options, COMMANDS
    from pyg.core import PygError, InstallationError, AlreadyInstalled, args_manager
    from pyg.log import logger

    try:
        if len(sys.argv) == 2 and sys.argv[-1] in ('-v', '--version'):
            logger.info(__version__)
            sys.exit(0)
        parser = init_parser(__version__)
        argv = argv or sys.argv[1:]
        if argv[0] not in COMMANDS:
            _proposals = [c for c in COMMANDS if c.startswith(argv[0])]
            if len(_proposals) == 1:
                argv[0] = _proposals[0]
            elif len(_proposals):
                logger.exit('Ambiguous command, "{0}" could be {1}'.format(argv[0], ' or '.join(_proposals)))
        args = parser.parse_args(argv)
        if args.verbose:
            logger.level = logger.VERBOSE
        if args.debug:
            logger.level = logger.DEBUG
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
    except Exception as e:
        if logger.level == logger.DEBUG:
            raise
        logger.exit('Unknown error occurred: {0}'.format(e))

    sys.exit(0)

if __name__ == '__main__':
    main()
