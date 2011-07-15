#!/usr/bin/env python
import os
import sys
import threading
import pypi_cache_server

cache = threading.Thread(target=pypi_cache_server.run)
cache.setDaemon(True)
cache.start()

try:
    from lettuce.lettuce_cli import main
except ImportError:
    want_install = raw_input("Lettuce package is not detected,\nauto-install (ONLY WORKS AS ADMIN) ? ") in 'yY'
else:
    want_install = False

if want_install:
    # backup python path & args before changing it
    sys_path = sys.path
    sys_argv = sys.argv
    sys.path.insert(0, os.path.abspath(os.path.pardir))
    # now the path is altered, import pyg
    import pyg
    # try to run lettuce's installation or upgrade
    try:
        sys.argv = ['pyg', 'install', '-A', 'lettuce']
        r = pyg.main()
    except (Exception, SystemExit) as e:
        print("Install failed ! Code:", e)
    else:
        if r:
            print("Install failed ! Code:", r)

    # restore standard variables
    sys.path = sys_path
    sys.argv = sys_argv
    from lettuce.lettuce_cli import main

# go to that file's folder and set KEEPENV if not set
os.chdir(os.path.dirname(os.path.abspath(__file__)))
if 'KEEPENV' not in os.environ:
    from tempfile import mkdtemp
    os.environ['KEEPENV'] = mkdtemp('_test_env', 'pyg_')

# start lettuce !
sys.exit(main())
