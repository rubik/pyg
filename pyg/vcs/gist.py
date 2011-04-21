import os
import sys
import shutil

try:
    import simplejson as json
except ImportError:
    import json

from pyg.inst import Installer
from pyg.utils import TempDir, name
from pyg.web import WebManager
from pyg.log import logger


SETUP_PY = '''## setup.py created by Pyg to install a Github Gist
from setuptools import setup

setup({0})
'''


class Gist(object):

    _data = None
    _files = None

    def __init__(self, gist_id):
        self.gist_id = str(gist_id)

    def __repr__(self):
        return '<Gist[{0}] at {1}>'.format(self.gist_id, id(self))

    @ property
    def data(self):
        if self._data is not None:
            return self._data
        url = 'https://gist.github.com/api/v1/json/{0}'.format(self.gist_id)
        self._data = json.loads(WebManager.request(url))
        return self._data

    @ property
    def files(self):
        if self._files is not None:
            return self._files
        self._files = self.data['gists'][0]['files']
        return self._files

    def get_file_content(self, filename):
        url = 'https://gist.github.com/raw/{0}/{1}'.format(self.gist_id, filename)
        return WebManager.request(url)

    def download(self, dest, accumulator):
        logger.info('Retrieving file names')
        for filename in self.files:
            logger.indent = 0
            logger.info('Downloading {0}', filename)
            logger.indent = 8
            path = os.path.abspath(os.path.join(dest, filename))
            if os.path.exists(path):
                while True:
                    u = raw_input('\tThe destination already exists: {0}\n\tWhat do you want to do?\n\n\t' \
                                  '(d)elete (b)ackup e(x)it\n\t> '.format(path)).lower()
                    if u == 'd':
                        logger.info('Removing {0}', path)
                        os.remove(path)
                        break
                    elif u == 'b':
                        d = path + '.pyg-backup'
                        logger.info('Moving {0} to {1}', path, d)
                        shutil.copyfile(path, d)
                        break
                    elif u == 'x':
                        logger.info('Exiting...')
                        sys.exit(0)
            with open(path, 'w') as f:
                logger.info('Writing data into {0}', filename)
                f.write(self.get_file_content(filename))
                accumulator.add(filename)


class GistInstaller(object):
    '''
    Install a Github Gist. ``url`` must be in the form::

        gist+{gist_id}#bin={bin1,bin2,binn}#mod={m1,m2,mn}
    '''

    def __init__(self, url):
        if url.startswith('gist+'):
            url = url[5:]
        parts = url.split('#')
        gist_id = parts[0]
        self.bin = self.mod = None
        for p in parts[1:]:
            if not p.strip():
                continue
            if p.startswith('bin='):
                self.bin = p[4:].split(',')
            elif p.startswith('mod='):
                self.mod = p[4:].split(',')
        self.gist = Gist(gist_id)
        if not self.bin and not self.mod:
            self.mod = map(name, self.gist.files)

    def setup_py(self):
        code = []
        if self.mod:
            code.append('py_modules=[{0}]'.format(repr(m) for m in self.mod))
        if self.bin:
            code.append('entry_points={\'console_scripts\': [{0}]}'.format(
                ', '.join(repr('{0} = {0}:main'.format(b)) for b in self.bin)))
        return SETUP_PY.format(', '.join(code))

    def install(self):
        with TempDir() as tempdir:
            acc = set()
            self.gist.download(tempdir, acc)
            files = [os.path.join(tempdir, f) for f in self.gist.files]
            filenames = self.gist.files
            with open(os.path.join(tempdir, 'setup.py'), 'w') as f:
                f.write(self.setup_py())
            Installer.from_dir(tempdir, 'gist {0}'.format(self.gist.gist_id))