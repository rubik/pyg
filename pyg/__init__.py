__version__ = '0.3.1'



def main():
    import os
    import sys
    import urllib2
    from parser.parser import init_parser
    from locations import CFG_FILES
    from types import PygError, InstallationError, AlreadyInstalled, args_manager

    try:
        parser = init_parser(__version__)
        for cfg in CFG_FILES:
            if os.path.exists(cfg):
                break
        args_manager.load(cfg)
        parser.dispatch()
    except (PygError, InstallationError, ValueError):
        sys.exit(1)
    except AlreadyInstalled:
        sys.exit(0)
    except urllib2.HTTPError as e:
        sys.exit(e.msg)
    except urllib2.URLError as e:
        sys.exit('urllib error: {0}'.format(e.reason))
    sys.exit(0)

if __name__ == '__main__':
    main()
