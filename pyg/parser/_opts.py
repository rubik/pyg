import re
import os
import functools
import pkg_resources

from pkgtools.pypi import PyPIXmlRpc

from pyg.vcs import vcs
from pyg.log import logger
from pyg.req import Requirement
from pyg.pack import Packer
from pyg.freeze import freeze, list_releases, site_info
from pyg.core import PygError, Version, args_manager
from pyg.inst import Installer, Uninstaller, Updater, Bundler
from pyg.utils import TempDir, is_installed, unpack
from pyg.web import ReqManager


def check_permissions(dir):
    if not os.path.exists(dir):
        logger.fatal('Error: installation directory {0} does not exist', dir, exc=PygError)
    try:
        path = os.path.join(dir, 'pyg-permissions-test.pth')
        with open(path, 'w'):
            pass
        os.remove(path)
    ## FIXME: Do we need OSError too?
    except (IOError, OSError):
        return False
    else:
        return True

def check_and_exit():
    dir = os.path.abspath(args_manager['install']['install_dir'])
    if not check_permissions(dir):
        logger.exit('''Pyg cannot create new files in the installation directory.
Installation directory was:

    {0}

Perhaps your account does not have write access to this directory?  If the
installation directory is a system-owned directory, you may need to sign in
as the administrator or "root" account.  If you do not have administrative
access to this machine, you may wish to choose a different installation
directory, preferably one that is listed in your PYTHONPATH environment
variable.

If you need further information about Pyg command-line options visit:

    http://pyg.readthedocs.org/en/latest/cmdline.html
or
    http://pyg-installer.co.nr
'''.format(dir))

def _install_package_from_name(package, ignore=False):
    if os.path.exists(package) and not ignore:
        path = os.path.abspath(package)
        logger.info('Installing {0}', path)
        if os.path.isfile(path):
            return Installer.from_file(path)
        elif os.path.isdir(path):
            if not os.path.exists(os.path.join(path, 'setup.py')):
                raise PygError('{0} must contain the setup.py file', path)
            return Installer.from_dir(path)
        else:
            raise PygError('Cannot install the package: {0} is neither a file nor a directory', path)
    if package.startswith(('http://', 'https://')):
        return Installer.from_url(package)
    for s in ('git+', 'hg+', 'bzr+', 'svn+'):
        if package.startswith(s):
            with TempDir() as tempdir:
                return vcs(package, tempdir).install()
    return Installer(package).install()

def install_func(packname, req_file, editable, ignore):
    check_and_exit()
    if editable:
        if len(packname) > 1:
            logger.error('Error: Unable to install multiple packages in editable mode')
            return
        package = packname[0]
        if os.path.exists(os.path.abspath(package)):
            package = 'dir+{0}#egg={1}'.format(os.path.abspath(package),
                                               os.path.basename(package))
        return vcs(package).develop()
    if req_file:
        logger.info('Installing from requirements file')
        for rq in req_file:
            Installer.from_req_file(os.path.abspath(rq))
        return
    if packname:
        for package in packname:
            _install_package_from_name(package, ignore)

def remove_func(packname, req_file, yes, info, local):
    uninstaller = functools.partial(Uninstaller, yes=yes, local=local)
    if info:
        for p in packname:
            logger.info('{0}:', p)
            files = uninstaller(p).find_files()
            logger.indent = 8
            for path in files:
                logger.info(path)
            logger.indent = 0
        return
    check_and_exit()
    ## Little Easter egg...
    if len(packname) == 1 and packname[0] == 'yourself':
        return uninstaller('pyg').uninstall()
    if req_file:
        with open(os.path.abspath(req_file)) as f:
            for line in f:
                try:
                    uninstaller(line.strip()).uninstall()
                except PygError:
                    continue
    for p in packname:
        try:
            uninstaller(p).uninstall()
        except PygError:
            continue

def check_func(name, info=False):
    INFO = '{0.project_name} - {0.version}\nInstalled in {0.location}'
    if not info:
        logger.info(is_installed(name))
        return
    if info:
        try:
            dist = pkg_resources.get_distribution(name)
            logger.info(INFO.format(dist))
        except pkg_resources.DistributionNotFound:
            logger.info(False)

def site_func(count, no_info, file):
    f = freeze()
    if count:
        logger.info(str(len(f)))
        return
    f = '\n'.join(f)
    if not no_info:
        f = site_info() + f
    if file:
        with open(os.path.abspath(file), 'w') as req_file:
            req_file.write(f)
    return logger.info(f)

def list_func(name):
    res = []
    for v, inst in list_releases(name):
        if inst:
            res.append(v + '\tinstalled')
        else:
            res.append(v)
    return logger.info('\n'.join(res))

def search_func(query, exact, show_all_version, max_num):
    def _pypi_order(item):
        # this is the old implementation, that looks buggy (try on "sphinx")
        return item['_pypi_ordering']

    def _pkgresources_order(item):
        return (item[0],) +  item[2].v

    res = sorted(PyPIXmlRpc(index_url=args_manager['install']['index_url']).search({'name': query, 'summary': query}, 'or'))
    processed = {}
    for release in res:
        name, version, summary = release['name'], Version(release['version']), release['summary']

        ## We have already parsed a different version
        if name in processed:
            if show_all_version:
                processed[name].append((version, summary))
            elif version > processed[name][0][0]:
                processed[name] = [(version, summary)]
            continue
        ## This is the first time
        processed[name] = [(version, summary)]

    pattern = re.compile('$|'.join(query) + '$')
    results = []
    for name, values in processed.iteritems():
        try:
            _installed = Version(pkg_resources.get_distribution(name).version)
        except pkg_resources.DistributionNotFound:
            _installed = None
        except Exception:
            logger.warn('WARN: Cannot get package data for {0!r}', name)
            _installed = None
        if exact:
            if pattern.match(name) is None:
                continue

        for version in values:
            if not _installed:
                dec = ''
            elif _installed == version[0]:
                dec = '@'
            else:
                dec = '*'
            results.append((name, dec, version[0], version[1]))

    results = sorted(results, key=_pkgresources_order)
    results = results[:max_num or len(results)]
    output = '\n'.join('{0}  {1}{2} - {3}'.format(name, dec, version, summary) for name, dec, version, summary in results)
    return logger.info(output)

def download_func(args):
    pref = None
    if args.prefer:
        pref = ['.' + args.prefer.strip('.')]
    name = args.packname
    dest = args_manager['download']['download_dir']
    unpk = args_manager['download']['unpack']
    downloader = ReqManager(Requirement(name), pref)
    if args_manager['download']['dry']:
        res = downloader.download(None)
    else:
        res = downloader.download(dest)

    if args_manager['download']['md5']:
        for dl in res:
            logger.info('%(url)s md5: %(hash)s'%dl)
    if downloader.downloaded_name is None:
        logger.fatal('Error: Did not find any files for {0}', name, exc=PygError)
    if unpk:
        path = os.path.abspath(downloader.downloaded_name)
        logger.info('Unpacking {0} to {1}', os.path.basename(path), os.getcwd())
        unpack(path)

def update_func():
    check_and_exit()
    up = Updater()
    up.update()

def bundle_func(packages, bundlename, exclude, req_file, develop):
    def get_reqs(path):
        path = os.path.abspath(path)
        reqs = set()
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                reqs.add(line)
        return reqs
    if not packages and not req_file:
        logger.fatal('Error: You must specify at least one package', exc=PygError)
    reqs = []
    if req_file:
        reqs = [Requirement(r) for f in req_file for r in get_reqs(f)]
    exclude = [Requirement(r) for r in (exclude or [])]
    bundlename = os.path.abspath(bundlename)
    dest, bundlename = os.path.dirname(bundlename), os.path.basename(bundlename)
    b = Bundler(map(Requirement, packages) + reqs, bundlename, exclude, use_develop=develop)
    b.bundle(dest=dest)

def pack_func(package, packname, exclude, use_develop):
    packname = os.path.abspath(packname)
    dest, packname = os.path.dirname(packname), os.path.basename(packname)
    exclude = [Requirement(r) for r in (exclude or [])]
    Packer(Requirement(package), packname, dest).gen_pack(exclude, use_develop)

def completion_func(commands, file):
    code = '''_pyg()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts=%r
    COMPREPLY=($(compgen -W "${opts}" -- "${cur}"))
}

complete -o default -F _pyg pyg'''

    code %= ' '.join(commands)

    if not file:
        return logger.info(code)

    dir = os.path.dirname(file)
    # permissions test
    try:
        path = os.path.join(dir, 'pyg-test')
        with open(path, 'w') as f:
            f.write('pyg test')
        os.remove(path)
    except IOError:
        logger.fatal('Pyg cannot write files into {0}.\nTry to run it with root privileges.', dir, exc=PygError)

    with open(file, 'a') as f:
        f.write('\n{0}\n'.format(code))
    os.system('source %s' % (file))

def shell_func():
    check_and_exit()

    from pyg.parser.shell import PygShell
    PygShell().cmdloop()
