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
from .web import Finder, WebManager


__all__ = ['Installer']


class Installer(object):
    def __init__(self, req):
        self.r = Requirement(req)
        self.f = Finder(self.r.name)

    def install(self):
        try:
            files, links = self.f.find()
        except urllib2.HTTPError as e:
            if e.code == 404:
                print '{0} not found'.format(self.r.name)
            else:
                print 'urllib2 returned error code: {0}'.format(e.code)
            return
        for ext in ('.egg', '.gz', '.bz2', '.zip'):
            arch = self.r.best_match(files[ext].keys())
            if arch is not None:
                return Installer.from_ext(ext, files[ext][arch])
        else:
            print '{0} not found'.format(self.r.name)

    @ classmethod
    def from_ext(cls, ext, file_url):
        url = file_url
        if file_url.startswith('../..'):
            url = 'http://pypi.python.org/' + file_url[6:]
        fobj = cStringIO.StringIO(WebManager.request(url))
        if ext in ('.gz', '.bz2', '.zip'):
            return Installer.from_arch(ext, fobj)
        elif ext == '.egg':
            name = url.split('/')[-1].split('.egg')[0] + '.egg'
            return Installer.from_egg(fobj, name)
        else:
            raise NotImplementedError('not implemented yet')

    @ staticmethod
    def from_file(filepath):
        ext = os.path.splitext(filepath)[1]
        if ext in ('.gz', '.bz2', '.zip'):
            return Installer.from_arch(ext, open(filepath))
        elif ext == '.egg':
            return Installer.from_egg(open(filepath))
        else:
            raise NotImplementedError('not implemented yet')

    @ staticmethod
    def from_egg(fobj, name):
        sitedir = site.getsitepackages()[0]
        egg = os.path.join(sitedir, name)
        print egg
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
            tempdir = tempfile.mkdtemp('-record', 'pyg-')
            recfile = os.path.join(tempdir, 'install_record')
            a.extractall(tempdir)
            fullpath = os.path.join(tempdir, os.listdir(tempdir)[0])
            cwd = os.getcwd()
            os.chdir(fullpath)
            args = ['python', 'setup.py', 'install', '--single-version-externally-managed', '--record', recfile]
            subprocess.call(args)
            os.chdir(cwd)
            shutil.rmtree(tempdir)

    @ staticmethod
    def from_bundle(filepath):
        raise NotImplementedError('not implemented yet')