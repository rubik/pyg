import os
import sys
import site
import platform


__all__ = ['under_virtualenv', 'INSTALL_DIR', 'USER_SITE', 'ALL_SITE_PACKAGES',
           'EASY_INSTALL', 'PYG_LINKS', 'BIN', 'HOME', 'PYG_HOME', 'CFG_FILES',
           'PYTHON_VERSION']


def under_virtualenv():
    return hasattr(sys, 'real_prefix')

PY_VERSION_INFO = sys.version_info[:2]
PYTHON_VERSION = ''.join(map(str, PY_VERSION_INFO))

INSTALL_DIR = None
if hasattr(site, 'getsitepackages'):
    INSTALL_DIR = site.getsitepackages()[0]
    USER_SITE = site.getusersitepackages()
    ALL_SITE_PACKAGES = site.getsitepackages() + [USER_SITE]

# XXX: WORKAROUND for older python versions and some broken virtualenvs
## we have to guess site packages location...
if INSTALL_DIR is None or not os.path.exists(INSTALL_DIR):
    USER_SITE = site.USER_SITE
    INSTALL_DIR = None
    system = platform.system()
    if system == 'Linux':
        tmp = ['{0}/lib/python{1}.{2}/'.format(sys.prefix, *PY_VERSION_INFO)]
        if not under_virtualenv():
            tmp.append('{0}/local/lib/python{1}.{2}/'.format(sys.prefix, *PY_VERSION_INFO))
        for dir in tmp:
            d, s = map(os.path.join, (dir, dir), ('dist-packages', 'site-packages'))
            if os.path.exists(d):
                INSTALL_DIR = d
                break
            elif os.path.exists(s):
                INSTALL_DIR = s
                break
    elif system == 'Windows':
        tmp = os.path.join(sys.prefix, 'site-packages')
        if os.path.exists(tmp):
            INSTALL_DIR = tmp
    if INSTALL_DIR is None:
        from distutils.sysconfig import get_python_lib
        INSTALL_DIR = get_python_lib(True)

    if under_virtualenv():
        ## Under virtualenv USER_SITE is the same as INSTALL_DIR
        USER_SITE = INSTALL_DIR
        ALL_SITE_PACKAGES = [INSTALL_DIR]
        local_site = os.path.join(sys.prefix, 'local', 'lib',
                                  'python{0}.{1}'.format(*PY_VERSION_INFO),
                                  os.path.basename(INSTALL_DIR)
                                  )
        if 'local' not in INSTALL_DIR.split(os.sep) and os.path.exists(local_site):
            ALL_SITE_PACKAGES.append(local_site)
    else:
        ALL_SITE_PACKAGES = [INSTALL_DIR, USER_SITE]

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


EASY_INSTALL = os.path.join(INSTALL_DIR, 'easy-install.pth')
if not os.path.exists(EASY_INSTALL):
    d = os.path.dirname(EASY_INSTALL)
    try:
        if not os.path.exists(d):
            os.makedirs(d)
        open(EASY_INSTALL, 'w').close()
    ## We do not have root permissions...
    except IOError:
        ## So we do nothing!
        pass

PYG_LINKS = os.path.join(USER_SITE, 'pyg-links.pth')

BIN2 = None
if platform.system() == 'Windows':
    BIN = os.path.join(sys.prefix, 'Scripts')
    if not os.path.exists(BIN):
        BIN = os.path.join(sys.prefix, 'bin')
else:
    BIN = os.path.join(sys.prefix, 'bin')
    ## Forcing to use /usr/local/bin on standard Mac OS X
    if sys.platform[:6] == 'darwin' and sys.prefix[:16] == '/System/Library/':
        BIN = '/usr/local/bin'
    local_bin = os.path.join(sys.prefix, 'local', 'bin')
    if 'local' not in BIN.split(os.sep) and os.path.exists(local_bin):
        BIN2 = local_bin


## If we are running on a Unix system and we are in a SUDO session the `SUDO_UID`
## environment variable will be set. We can use that to get the user's home
## We also set to None all the variables that depend on HOME.

## Look for environment variables: HOME, PYG_CONFIG_FILE, 
HOME = os.getenv('HOME')
CFG_FILES = os.getenv('PYG_CONFIG_FILE')
if CFG_FILES is not None:
    CFG_FILES = CFG_FILES.split(':')
else:
    CFG_FILES = []
CFG_FILES.append(os.path.join(os.getcwd(), 'pyg.conf'))

## Look for SUDO_UID environment variable (Unix)
_sudo_uid = os.getenv('SUDO_UID')
if _sudo_uid:
    import pwd
    _sudo_uid = int(_sudo_uid)
    HOME = pwd.getpwuid(_sudo_uid).pw_dir
if HOME is not None:
    CFG_FILES.append(os.path.join(HOME, 'pyg.conf'))

## Here is Pyg's HOME directory
## If it does not exists we create it
PYG_HOME = os.getenv('PYG_HOME')
if PYG_HOME is None and HOME is not None:
    PYG_HOME = os.path.join(HOME, '.pyg')
if PYG_HOME and not os.path.exists(PYG_HOME):
    os.makedirs(PYG_HOME)
## PACKAGES_CACHE has been removed because with `pkg_resources.working_set` we
## don't need a cache
if PYG_HOME is not None:
    CFG_FILES.append(os.path.join(PYG_HOME, 'pyg.conf'))
