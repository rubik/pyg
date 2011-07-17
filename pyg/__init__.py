__version__ = 'dev'


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
        parser = init_parser(__version__)
        args = parser.parse_args(argv or sys.argv[1:])
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
