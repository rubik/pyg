import os
import pwd
import sys
import site
import platform


if sys.version_info[:2] < (2, 7):
    ## Since the site module hasn't the getsitepackages() function (in Python < 2.7)
    ## we have to guess it.
    USER_SITE = site.USER_SITE
    INSTALL_DIR = None
    system = platform.system()
    if system == 'Linux':
        tmp = '{0}/local/lib/python{1}.{2}/'.format(sys.prefix, *sys.version_info[:2])
        d, s = os.path.join(tmp, 'dist-packages'), os.path.join(tmp, 'site-packages')
        if os.path.exists(d):
            INSTALL_DIR = d
        elif os.path.exists(s):
            INSTALL_DIR = s
    elif system == 'Windows':
        tmp = os.path.join(sys.prefix, 'site-packages')
        if os.path.exists(tmp):
            INSTALL_DIR = tmp
    if INSTALL_DIR is None:
        from distutils.sysconfig import get_python_lib
        INSTALL_DIR = get_python_lib(True)

    #try:
    #    INSTALL_DIR = sorted([p for p in sys.path if p.endswith('dist-packages')],
    #                        key=lambda i: 'local' in i, reverse=True)[0]
    #except IndexError:
    #    pass
    #if not INSTALL_DIR: ## Are we on Windows?
    #    try:
    #        INSTALL_DIR = sorted([p for p in sys.path if p.endswith('site-packages')],
    #                        key=lambda i: 'local' in i, reverse=True)[0]
    #    except IndexError:
    #        pass
    #if not INSTALL_DIR: ## We have to use /usr/lib/pythonx.y/dist-packages or something similar
    #    from distutils.sysconfig import get_python_lib
    #    INSTALL_DIR = get_python_lib()
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


## If we are running on a *nix system and we are in a SUDO session the `SUDO_UID`
## environment variable will be set. We can use that to get the user's home
## We also set to None all the variables that depend on HOME.
HOME = os.getenv('HOME')
PYG_HOME = PACKAGES_CACHE = None
_sudo_uid = os.getenv('SUDO_UID')
if _sudo_uid:
    _sudo_uid = int(_sudo_uid)
    HOME = pwd.getpwuid(_sudo_uid).pw_dir

## Here is Pyg's HOME directory
## If it does not exists we create it
if HOME:
    PYG_HOME = os.path.join(HOME, '.pyg')
    if not os.path.exists(PYG_HOME):
        os.makedirs(PYG_HOME)

    ## Now let's look for `installed_packages.txt` file
    ## At the moment we don't care wheter it exists or not,
    ## this will be checked by `pyg.inst.Updater`
    PACKAGES_CACHE = os.path.join(PYG_HOME, 'installed_packages.txt')
