import sys
import shutil
import urllib2
import os.path
import zipfile
import tarfile
import tempfile
import cStringIO
import subprocess

from .req import Requirement
from .web import Finder, request


__all__ = ['Installer']


class Installer(object):
    def __init__(self, req):
        self.r = Requirement(req)
        self.f = Finder(self.r.name)

    @ classmethod
    def from_ext(cls, ext, file_url):
        url = file_url
        if file_url.startswith('../..'):
            url = 'http://pypi.python.org/' + file_url[6:]
        print url
        fobj = cStringIO.StringIO(request(url))
        if ext in ('.gz', '.bz2', '.zip'):
            return Installer.from_arch(ext, fobj)
        elif ext == '.egg':
            return Installer.from_egg(fobj)
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
    def from_egg(fobj):
        return NotImplemented

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

    def install(self):
        try:
            files, links = self.f.find()
        except urllib2.HTTPError as e:
            if e.code == 404:
                print '{0} not found'.format(self.r.name)
            else:
                print 'urllib2 returned error code: {0}'.format(e.code)
            return
        for ext in ('.gz', '.bz2', '.zip', '.egg'):
            arch = self.r.best_match(files[ext].keys())
            if arch is not None:
                return Installer.from_ext(ext, files[ext][arch])
        else:
            print '{0} not found'.format(self.r.name)