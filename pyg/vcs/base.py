import os
import sys
import shutil

from pyg.utils import TempDir, ChDir, call_subprocess, call_setup
from pyg.inst import Installer
from pyg.core import InstallationError
from pyg.log import logger


class VCS(object):

    ARGS = None

    def __init__(self, dest, skip=False):
        self.dest = os.path.abspath(dest)
        self.skip = skip

    def __repr__(self):
        return '<{0}[{1}] object at {2}>'.format(self.__class__.__name__,
                                                 self.package_name,
                                                 id(self))

    @ property
    def cmd(self):
        return self.CMD

    @ property
    def method(self):
        return self.METHOD

    @ property
    def dir(self):
        try:
            return os.path.join(self.dest, os.listdir(self.dest)[0])
        except OSError:
            return None

    def parse_url(self, url):
        if not '#egg=' in url:
            raise ValueError('You must specify #egg=PACKAGE')
        return url.split('#egg=')

    def retrieve_data(self):
        self.call_cmd([self.url])

    def check_dest(self):
        if self.skip:
            return
        if os.path.exists(self.dest):
            while True:
                u = raw_input('The destination already exists: {0}\nWhat do you want to do?\n\n' \
                              '(d)elete, (b)ackup, e(x)it\n> '.format(self.dest)).lower()
                if u == 'd':
                    logger.info('Removing {0}...', self.dest)
                    shutil.rmtree(self.dest)
                    os.makedirs(self.dest)
                    break
                elif u == 'b':
                    dst = os.path.join(os.path.dirname(self.dest),
                                                        self.dest + '-pyg-backup')
                    logger.info('Moving {0} to {1}', self.dest, dst)
                    shutil.move(self.dest, dst)
                    os.makedirs(self.dest)
                    break
                elif u == 'x':
                    logger.info('Exiting...')
                    sys.exit(0)
        else:
            os.makedirs(self.dest)

    def call_cmd(self, args):
        self.check_dest()
        with TempDir() as tempdir:
            with ChDir(self.dest):
                if self.ARGS is not None:
                    args = ARGS + args
                logger.info('Copying data from {0} to {1}', self.url, self.dest)
                if call_subprocess([self.cmd, self.method] + args, sys.stdout, sys.stderr) != 0:
                    logger.fatal('Error: Cannot retrieve data', exc=InstallationError)

    def develop(self):
        self.retrieve_data()
        if not os.path.exists(os.path.join(self.dir, 'setup.py')):
            logger.fatal('Error: The repository must have a top-level setup.py file', exc=InstallationError)
        logger.info('Running setup.py develop for {0}', self.package_name)
        if call_setup(self.dir, ['develop']) != 0:
            return
        logger.info('{0} installed succesfully', self.package_name)

    def install(self):
        self.retrieve_data()
        Installer.from_dir(self.dir, self.package_name)