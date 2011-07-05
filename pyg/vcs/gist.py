import os
import sys
import shutil

try:
    import simplejson as json
except ImportError:
    import json

from pyg.inst import Installer
from pyg.utils import TempDir
from pyg.web import request
from pyg.log import logger


class Gist(object):

    _data = None
    _files = None

    def __init__(self, gist_id):
        self.gist_id = str(gist_id)

    def __repr__(self):
        return '<Gist[{0}] at {1}>'.format(self.gist_id, id(self))

    @property
    def data(self):
        if self._data is not None:
            return self._data
        url = 'https://gist.github.com/api/v1/json/{0}'.format(self.gist_id)
        self._data = json.loads(request(url))
        return self._data

    @property
    def files(self):
        if self._files is not None:
            return self._files
        self._files = self.data['gists'][0]['files']
        return self._files

    def get_file_content(self, filename):
        url = 'https://gist.github.com/raw/{0}/{1}'.format(self.gist_id, filename)
        return request(url)

    def download(self, dest, accumulator):
        logger.info('Retrieving file names')
        for filename in self.files:
            logger.indent = 0
            logger.info('Downloading {0}', filename)
            logger.indent = 8
            path = os.path.abspath(os.path.join(dest, filename))
            if os.path.exists(path):
                txt = 'The destination already exists: {0}\nWhat do you want to do'.format(path)
                u = logger.ask(txt, choices={'destroy': 'd', 'backup': 'b', 'exit': 'x'})

                if u == 'd':
                    logger.info('Removing {0}', path)
                    os.remove(path)
                elif u == 'b':
                    d = path + '.pyg-backup'
                    logger.info('Moving {0} to {1}', path, d)
                    shutil.copyfile(path, d)
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

        gist+{gist_id}
    '''

    def __init__(self, url):
        if url.startswith('gist+'):
            url = url[5:]
        self.gist = Gist(url)

    def install(self):
        with TempDir() as tempdir:
            acc = set()
            self.gist.download(tempdir, acc)
            if 'setup.py' not in self.gist.files:
                logger.fatal('Error: gist must contain at least the `setup.py` file')
            Installer.from_dir(tempdir, 'gist {0}'.format(self.gist.gist_id))