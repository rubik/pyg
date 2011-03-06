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
from .utils import is_installed, home, TempDir

try:
    from hashlib import md5
except ImportError:
    from md5 import md5


__all__ = ['Installer']


class Installer(object):
    def __init__(self, req, mode='inst'):
        if mode == 'inst' and is_installed(str(req)):
            print '{0} is already installed, exiting now...'.format(req)
            sys.exit(0)
        try:
            self.w = WebManager(req)
        except urllib2.HTTPError as e:
            print 'E: urllib2 returned error code: {0}. Message: {1}'.format(e.code, e.msg)
            sys.exit(1)
        self.name = self.w.name

    def install(self):
        try:
            files = self.w.find()
        except urllib2.HTTPError as e:
            print 'E: urllib2 returned error code: {0}'.format(e.code)
            return
        for version, name, md5_hash, url in files:
            if name.endswith('.egg'):
                vcode = 'py{0}'.format('.'.join(map(str, sys.version_info[:2])))
                if vcode not in name:
                    continue
            try:
                return Installer.from_ext(name, md5_hash, url)
            except:
                continue
        else:
            print '{0} not found'.format(self.name)
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
            print 'Did not find any file to delete'
            sys.exit(1)
        print 'Uninstalling {0}'.format(self.name)
        print '\t' + '\n\t'.join(to_del)
        while True:
            u = raw_input('Proceed? (y/[n]) ')
            if u in ('n', ''):
                print '{0} has not been uninstalled'.format(self.name)
                sys.exit(0)
            elif u == 'y':
                for d in to_del:
                    try:
                        shutil.rmtree(d)
                    except OSError: ## It is not a directory
                        os.remove(d)
                    print 'Deleting: {0}...'.format(d)
                print '{0} uninstalled succesfully'.format(self.name)
                sys.exit(0)

    @ classmethod
    def from_ext(cls, filename, md5_hash, file_url):
        url = file_url
        if file_url.startswith('../..'):
            url = 'http://pypi.python.org/' + file_url[6:]
        fobj = cStringIO.StringIO(WebManager.request(url))
        if md5(fobj.getvalue()).hexdigest() != md5_hash:
            print '{0} appears to be corrupted'.format(self.name)
            raise Exception('E: Cannot continue: {0} appears to be corrupted'.format(self.name))
        ext = os.path.splitext(filename)[1]
        if ext in ('.gz', '.bz2', '.zip'):
            return Installer.from_arch(ext, fobj)
        elif ext == '.egg':
            return Installer.from_egg(fobj, name)
        else:
            raise NotImplementedError('not implemented yet')

    @ staticmethod
    def from_file(filepath):
        ext = os.path.splitext(filepath)[1]
        if ext in ('.gz', '.bz2', '.zip'):
            return Installer.from_arch(ext, open(filepath))
        elif ext == '.egg':
            return Installer.from_egg(open(filepath), os.path.basename(filepath))
        elif ext == '.pybundle':
            return Installer.from_bundle(open(filepath))
        else:
            raise NotImplementedError('not implemented yet')

    @ staticmethod
    def from_egg(fobj, name):
        sitedir = site.getsitepackages()[0]
        egg = os.path.join(sitedir, name)
        if os.path.exists(egg):
            print '{0} is already installed'.format(sys.argv[-1])
            return
        os.makedirs(egg)
        with zipfile.ZipFile(fobj) as z:
            z.extractall(egg)
            with open(os.path.join(sitedir, 'easy-install.pth')) as f:
                lines = f.readlines()
            with open(os.path.join(sitedir, 'easy-install.pth'), 'w') as f:
                last = lines[-1]
                f.writelines(lines[:-1])
                f.write('./' + name + '\n')
                f.write(last)

    @ staticmethod
    def from_arch(ext, fobj):
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
                args = ['python', 'setup.py', 'egg_info', 'install',
                        '--single-version-externally-managed', '--record', recfile]
                subprocess.call(args)
                os.chdir(cwd)

    @ staticmethod
    def from_bundle(filepath):
        with zipfile.ZipFile(filepath) as z:
            with TempDir() as tempdir:
                z.extractall(tempdir)
                location = os.path.join(tempdir, os.path.abspath(filepath))
                manifest = os.path.join(location, 'pip-manifest.txt')
                raise NotImplementedError('not implemented yet')