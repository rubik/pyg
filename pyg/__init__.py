__version__ = '0.5'


def main():
    import sys
    import urllib2

    from .parser.parser import init_parser, load_options
    from .core import PygError, InstallationError, AlreadyInstalled

    try:
        parser = init_parser(__version__)
        load_options()
        parser.dispatch()
    except (PygError, InstallationError, ValueError):
        sys.exit(1)
    except AlreadyInstalled:
        sys.exit(0)
    except urllib2.HTTPError as e:
        sys.exit('HTTPError: {0}'.format(e.msg))
    except urllib2.URLError as e:
        sys.exit('urllib error: {0}'.format(e.reason))
    sys.exit(0)

if __name__ == '__main__':
    main()
