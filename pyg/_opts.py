import os
import sys
import urllib2

from .log import logger
from .freeze import freeze
from .req import Requirement
from .inst import Installer, Uninstaller
from .web import PREFERENCES, PyPI, WebManager, PackageManager
from .utils import USER_SITE, PYG_LINKS, is_installed, link, unlink


def install_from_name(name):
    return Installer(name).install()

def install_func(args):
    if args.develop:
        raise NotImplementedError('not implemented yet')
    if args.file:
        return Installer.from_file(args.packname)
    if args.req_file:
        return Installer.from_req_file(args.packname)
    return install_from_name(args.packname)

def uninst_func(args):
    return Uninstaller(args.packname).uninstall()

def link_func(args):
    return link(args.path)

def unlink_func(args):
    if args.all:
        return os.remove(pyg_links())
    return unlink(args.path)

def freeze_func(args):
    f = freeze()
    if args.count:
        sys.stdout.write(str(len(freeze())) + '\n')
        return
    f = '\n'.join(f) + '\n'
    if args.file:
        with open(os.path.abspath(args.file), 'w') as req_file:
            req_file.write(f)
    return sys.stdout.write(f)

def list_func(args):
    res = []
    name = args.packname
    versions = PyPI().package_releases(name, True)
    if not versions:
        versions = map(str, sorted(WebManager.versions_from_html(name), reverse=True))
    for v in versions:
        if is_installed('{0}=={1}'.format(name, v)):
            res.append(v + '\tinstalled')
        else:
            res.append(v)
    return sys.stdout.write('\n'.join(res) + '\n')

def search_func(args):
    res = PyPI().search({'name': args.packname})
    return sys.stdout.write('\n'.join('{name}  {version} - {summary}'.format(**i) for i in \
                            sorted(res, key=lambda i: i['_pypi_ordering'], reverse=True)) + '\n')

def download_func(args):
    packname = args.packname
    pref = None
    if args.prefer:
        pref = ['.' + args.prefer.strip('.')]

    dest = os.path.abspath(args.download_dir)
    try:
        pman = PackageManager(Requirement(packname), pref)
    except urllib2.HTTPError as e:
        logger.fatal('E: {0}'.format(e.msg))
        sys.exit(1)
    files = pman.arrange_files()

    if not files:
        logger.error('E: Did not find files to download')
        sys.exit(1)
    
    ## We need a placeholder because of the nested for loops
    success = False

    for p in pman.pref:
        if success:
            break
        for v, name, hash, url in files[p]:
            try:
                data = WebManager.request(url)
            except (urllib2.URLError, urllib2.HTTPError) as e:
                logger.debug('urllib2 error: {0}'.format(e.args))
                continue
            if not data:
                logger.debug('request failed')
                continue
            if not os.path.exists(dest):
                os.makedirs(dest)
            logger.info('Retrieving data for {0}'.format(packname))
            try:
                logger.info('Writing data into {0}'.format(name))
                with open(os.path.join(dest, name), 'w') as f:
                    f.write(data)
            except (IOError, OSError):
                logger.debug('error while writing data')
                continue
            logger.info('{0} downloaded successfully'.format(packname))
            success = True