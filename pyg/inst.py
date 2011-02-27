import shutil
import os.path
import tarfile
import tempfile
import cStringIO
import subprocess

from .req import Requirement
from .web import Finder, request


class Installer(object):
    def __init__(self, req):
        self.r = Requirement(req)
        self.f = Finder(self.r.name)

    @ classmethod
    def from_ext(cls, ext, file_url):
        MAP = {'.gz': 'from_tar_gz',
               '.zip': 'from_zip',
               '.bz2': 'from_bz2',
               '.egg': 'from_egg'
               }
        url = file_url
        if file_url.startswith('../..'):
            url = 'http://pypi.python.org/' + file_url[6:]
        fobj = cStringIO.StringIO(request(url))
        return getattr(cls, MAP[ext])(fobj)

    @ staticmethod
    def from_tar_gz(fobj):
        with tarfile.open(fileobj=fobj, mode='r:gz') as t:
            tempdir = tempfile.mkdtemp()
            t.extractall(tempdir)
            subprocess.call(['python', os.path.join(tempdir, os.listdir(tempdir)[0], 'setup.py'), 'install'])
            shutil.rmtree(tempdir)

    def install(self):
        files, links = self.f.find()
        for ext in ('.gz', '.zip', '.bz2', '.egg'):
            arch = self.r.best_match(files[ext].keys())
            if arch is not None:
                return Installer.from_ext(ext, files[ext][arch])
        else:
            print 'Not found'