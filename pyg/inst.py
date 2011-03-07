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
from .utils import is_installed, home, TempDir

try:
    from hashlib import md5
except ImportError:
    from md5 import md5


__all__ = ['Installer']


class Installer(object):
    def __init__(self, req, mode='inst'):
        if mode == 'inst' and is_installed(str(req)):
            logger.notify('{0} is already installed, exiting now...'.format(req))
            sys.exit(0)
        try:
            self.w = WebManager(req)
        except urllib2.HTTPError as e:
            logger.fatal('urllib2 returned error code: {0}. Message: {1}'.format(e.code, e.msg))
            sys.exit(1)
        self.name = self.w.name

    def install(self):
        try:
            files = self.w.find()
        except urllib2.HTTPError as e:
            logger.fatal('E: urllib2 returned error code: {0}'.format(e.code))
            return
        for version, name, md5_hash, url in files:
            if name.endswith('.egg'):
                vcode = 'py{0}'.format('.'.join(map(str, sys.version_info[:2])))
                if vcode not in name:
                    continue
            return self.from_ext(name, md5_hash, url)
        else:
            logger.error('{0} not found'.format(self.name))
            sys.exit(1)

    def uninstall(self):
        uninstall_re = re.compile(r'{0}(-(\d\.?)+(\-py\d\.\d)?\.(egg|egg\-info))?'.format(self.name), re.I)
        guesses = site.getsitepackages() + [site.getusersitepackages()]
        to_del = []
        for d in guesses:
            try:
                for file in os.listdir(d):
                    if uninstall_re.match(file):
                        to_del.append(os.path.join(d, file))
            except OSError:
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
                logger.notify('{0} uninstalled succesfully'.format(self.name))
                sys.exit(0)

    def from_ext(self, filename, md5_hash, file_url):
        url = file_url
        if file_url.startswith('../..'):
            url = 'http://pypi.python.org/' + file_url[6:]
        logger.notify('Downloading {0}'.format(self.name))
        fobj = cStringIO.StringIO(WebManager.request(url))
        if md5(fobj.getvalue()).hexdigest() != md5_hash:
            logger.fatal('{0} appears to be corrupted'.format(self.name))
            raise Exception('E: Cannot continue: {0} appears to be corrupted'.format(self.name))
        ext = os.path.splitext(filename)[1]
        if ext in ('.gz', '.bz2', '.zip'):
            return self.from_arch(ext, fobj)
        elif ext == '.egg':
            return self.from_egg(fobj, name)
        else:
            raise NotImplementedError('not implemented yet')

    def from_egg(self, fobj, name):
        sitedir = site.getsitepackages()[0]
        egg = os.path.join(sitedir, name)
        if os.path.exists(egg):
            logger.notify('{0} is already installed'.format(sys.argv[-1]))
            return
        os.makedirs(egg)
        logger.notify('Unpacking egg for {0}'.format(self.name))
        with zipfile.ZipFile(fobj) as z:
            z.extractall(egg)
            logger.notify('Installing {0} egg file'.format(self.name))
            with open(os.path.join(sitedir, 'easy-install.pth')) as f: ## TODO: Fix the opening mode to read and write simultaneously
                lines = f.readlines()
            with open(os.path.join(sitedir, 'easy-install.pth'), 'w') as f:
                last = lines[-1]
                f.writelines(lines[:-1])
                f.write('./' + name + '\n')
                f.write(last)

    def from_arch(self, ext, fobj):
        logger.notify('Unpacking {0}'.format(self.name))
        if ext == '.zip':
            arch = zipfile.ZipFile(fobj)
        else:
            arch = tarfile.open(fileobj=fobj, mode='r:{0}'.format(ext[1:]))
        with arch as a:
            with TempDir() as tempdir:
                recfile = os.path.join(home(), '.pyg', '.pyg-install-record')
                a.extractall(tempdir)
                fullpath = os.path.join(tempdir, os.listdir(tempdir)[0])
                cwd = os.getcwd()
                os.chdir(fullpath)
                logger.notify('Running setup.py for {0}'.format(self.name))
                args = ['python', 'setup.py', 'egg_info', 'install',
                        '--single-version-externally-managed', '--record', recfile]
                subprocess.call(args, stdout=subprocess.PIPE)
                os.chdir(cwd)

    def from_file(self, filepath):
        ext = os.path.splitext(filepath)[1]
        if ext in ('.gz', '.bz2', '.zip'):
            return self.from_arch(ext, open(filepath))
        elif ext in ('.pybundle', '.pyb'):
            return self.from_bundle(filepath)
        elif ext == '.egg':
            return self.from_egg(open(filepath), os.path.basename(filepath))
        else:
            raise NotImplementedError('not implemented yet')

    def from_bundle(self, filepath):
        with zipfile.ZipFile(filepath) as z:
            with TempDir() as tempdir:
                z.extractall(tempdir)
                location = os.path.join(tempdir, os.path.abspath(filepath))
                pip_manifest = os.path.join(location, 'pip-manifest.txt')
                if os.path.exists(os.path.join(location, 'MANIFEST')):
                    manifest = os.path.join(location, 'MANIFEST')
                raise NotImplementedError('not implemented yet')
