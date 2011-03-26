import os
import sys
import site


if sys.version_info[:2] < (2, 7):
    USER_SITE = site.USER_SITE
    INSTALL_DIR = None
    try:
        INSTALL_DIR = sorted([p for p in sys.path if p.endswith('dist-packages')],
                            key=lambda i: 'local' in i, reverse=True)[0]
    except IndexError:
        pass
    if not INSTALL_DIR: ## Are we on Windows?
        try:
            INSTALL_DIR = sorted([p for p in sys.path if p.endswith('site-packages')],
                            key=lambda i: 'local' in i, reverse=True)[0]
        except IndexError:
            pass
    if not INSTALL_DIR: ## We have to use /usr/lib/pythonx.y/dist-packages or something similar
        from distutils.sysconfig import get_python_lib
        INSTALL_DIR = get_python_lib()
else:
    INSTALL_DIR = site.getsitepackages()[0]
    USER_SITE = site.getusersitepackages()

EASY_INSTALL = os.path.join(INSTALL_DIR, 'easy-install.pth')
if not os.path.exists(EASY_INSTALL):
    d = os.path.dirname(EASY_INSTALL)
    try:
        if not os.path.exists(d):
            os.makedirs(d)
        open(EASY_INSTALL, 'w').close()
    ## We do not have root permissions...
    except IOError:
        ## So we do not create the file!
        pass

PYG_LINKS = os.path.join(USER_SITE, 'pyg-links.pth')

if sys.platform == 'win32':
    BIN = os.path.join(sys.prefix, 'Scripts')
    if not os.path.exists(BIN):
        BIN = os.path.join(sys.prefix, 'bin')
else:
    BIN = os.path.join(sys.prefix, 'bin')
    ## Forcing to use /usr/local/bin on standard Mac OS X
    if sys.platform[:6] == 'darwin' and sys.prefix[:16] == '/System/Library/':
        BIN = '/usr/local/bin'