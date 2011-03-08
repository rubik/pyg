import re
import sys
import site
import shutil
import urllib2
import os.path
import zipfile
import tarfile
import tempfile
import cStringIO
import subprocess

from .req import Requirement
from .web import WebManager
from .log import logger
from .utils import is_installed, name_from_egg, call_setup, TempDir, INSTALL_DIR, EASY_INSTALL

try:
    from hashlib import md5
except ImportError:
    from md5 import md5


__all__ = ['Installer', 'Uninstaller', 'Egg', 'Archive']


class Installer(object):
    def __init__(self, req):
        if is_installed(str(req)):
            logger.notify('{0} is already installed, exiting now...'.format(req))
            sys.exit(0)
        try:
            self.w = WebManager(req)
        except urllib2.HTTPError as e:
            logger.fatal('E: urllib2 returned error code: {0}. Message: {1}'.format(e.code, e.msg))
            sys.exit(1)
        self.name = self.w.name

    def install(self):
        try:
            files = self.w.find()
        except urllib2.HTTPError as e:
            logger.fatal('E: urllib2 returned error code: {0}. Message: {1}'.format(e.code, e.msg))
            return
        for version, name, md5_hash, url in files:
            if name.endswith('.egg'):
                vcode = 'py{0}'.format('.'.join(map(str, sys.version_info[:2])))
                if vcode not in name:
                    continue
            if self.from_ext(name, md5_hash, url) == 0:
                return 0
        else:
            ## TODO: We have to check downloads links before throwing error
            logger.error('{0} not found'.format(self.name))
            sys.exit(1)

    def from_ext(self, filename, md5_hash, file_url):
        url = file_url
        if file_url.startswith('../..'):
            url = 'http://pypi.python.org/' + file_url[6:]
        logger.notify('Downloading {0}'.format(self.name))
        fobj = cStringIO.StringIO(WebManager.request(url))
        if md5(fobj.getvalue()).hexdigest() != md5_hash:
            logger.fatal('E: {0} appears to be corrupted'.format(self.name))
            sys.exit(1)
        ext = os.path.splitext(filename)[1]
        if ext in ('.gz', '.bz2', '.zip'):
            return Installer.from_arch(fobj, ext, self.name)
        elif ext == '.egg':
            return Installer.from_egg(fobj, name, self.name)
        else:
            raise NotImplementedError('not implemented yet')

    @ staticmethod
    def from_egg(fobj, eggname, packname=None):
        e = Egg(fobj, eggname, packname)
        if e.install() != 0:
            logger.fatal('E: Egg file not installed')
            sys.exit(1)
        logger.notify('Egg file installed successfully')
        return 0

    @ staticmethod
    def from_arch(fobj, ext, name):
        a = Archive(fobj, ext, name)
        if a.install() != 0:
            logger.fatal('E: Package not installed')
            sys.exit(1)
        logger.notify('Package installed succesfully')
        return 0

    @ staticmethod
    def from_file(filepath):
        ext = os.path.splitext(filepath)[1]
        path = os.path.abspath(filepath)
        packname = os.path.basename(filepath)
        if ext in ('.gz', '.bz2', '.zip'):
            return Installer.from_arch(open(path), ext, packname)
        elif ext in ('.pybundle', '.pyb'):
            return Installer.from_bundle(filepath)
        elif ext == '.egg':
            Installer.from_egg(open(path), path)
        sys.exit(0)

    @ staticmethod
    def from_bundle(filepath):
        path = os.path.abspath(filepath)
        with TempDir() as tempdir:
            with zipfile.ZipFile(path) as z:
                z.extractall(tempdir)
            location = os.path.join(tempdir, 'build')
            pip_manifest = os.path.join(tempdir, 'pip-manifest.txt')
            with open(pip_manifest) as pf:
                lines = pf.readlines()[4:]
                main_pack, deps = [], []
                current = main_pack
                for line in lines:
                    if line.startswith('#'):
                        current = deps
                        continue
                    current.append(line.split('==')[0])
            for d in deps:
                l = os.path.join(location, d)
                logger.notify('Calling setup.py for {0}'.format(d))
                call_setup(l)
                logger.notify('{0}: installed'.format(d))
            logger.notify('Finished processing dependencies')
            logger.notify('Installing main package')
            for p in main_pack:
                l = os.path.join(location, p)
                logger.notify('Calling setup.py for {0}'.format(p))
                call_setup(l)
            logger.info('Bundle installed successfully')


class Uninstaller(object):
    def __init__(self, packname):
        self.name = packname

    def uninstall(self):
        uninstall_re = re.compile(r'{0}(-(\d\.?)+(\-py\d\.\d)?\.(egg|egg\-info))?'.format(self.name), re.I)
        path_re = re.compile('./{0}-[\d\w\.]+-py\d\.\d.egg'.format(self.name))
        guesses = site.getsitepackages() + [site.getusersitepackages()]
        to_del = []
        for d in guesses:
            try:
                for file in os.listdir(d):
                    if uninstall_re.match(file):
                        to_del.append(os.path.join(d, file))
            except OSError: ## os.listdir
                continue
        if not to_del:
            logger.warn('Did not find any file to delete')
            sys.exit(1)
        logger.notify('Uninstalling {0}'.format(self.name))
        logger.indent += 8
        for d in to_del:
            logger.info(d)
        logger.indent -= 8
        while True:
            u = raw_input('Proceed? (y/[n]) ')
            if u in ('n', ''):
                logger.info('{0} has not been uninstalled'.format(self.name))
                sys.exit(0)
            elif u == 'y':
                for d in to_del:
                    try:
                        shutil.rmtree(d)
                    except OSError: ## It is not a directory
                        os.remove(d)
                    logger.notify('Deleting: {0}...'.format(d))
                logger.notify('Removing eggs from easy_install.pth...')
                with open(EASY_INSTALL) as f:
                    lines = f.readlines()
                with open(EASY_INSTALL, 'w') as f:
                    for line in lines:
                        if not path_re.match(line):
                            f.write(line)
                logger.notify('{0} uninstalled succesfully'.format(self.name))
                sys.exit(0)


class Egg(object):
    def __init__(self, fobj, eggname, packname=None):
        self.fobj = fobj
        self.eggname = os.path.basename(eggname)
        self.packname = packname or name_from_egg(eggname)
        self.idir = INSTALL_DIR
        print self.eggname, self.packname, self.idir

    def install(self):
        eggpath = os.path.join(self.idir, self.eggname)
        if os.path.exists(eggpath):
            print eggpath
            logger.notify('{0} is already installed'.format(self.packname))
            return 0
        logger.notify('Installing {0} egg file'.format(self.packname))
        with zipfile.ZipFile(self.fobj) as z:
            z.extractall(os.path.join(self.idir, self.eggname))
        with open(EASY_INSTALL) as f: ## TODO: Fix the opening mode to read and write simultaneously
            lines = f.readlines()
        with open(EASY_INSTALL, 'w') as f:
            f.writelines(lines[:-1])
            f.write('./' + self.eggname + '\n')
            f.write(lines[-1])
        return 0


class Archive(object):
    def __init__(self, fobj, ext, name):
        self.name = name
        if ext == '.zip':
            self.arch = zipfile.ZipFile(fobj)
        else:
            self.arch = tarfile.open(fileobj=fobj, mode='r:{0}'.format(ext[1:]))

    def install(self):
        try:
            with TempDir() as tempdir:
                with self.arch as a:
                    a.extractall(tempdir)
                fullpath = os.path.join(tempdir, os.listdir(tempdir)[0])
                logger.notify('Running setup.py for {0}'.format(self.name))
                call_setup(fullpath)
        except Exception as e: ## Ugly but necessary
            return 1
        else:
            return 0
