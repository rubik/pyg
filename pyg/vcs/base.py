import os
import sys
import shutil

from pyg.utils import TempDir, ChDir, call_subprocess, call_setup
from pyg.inst import Installer
from pyg.types import InstallationError
from pyg.log import logger


class VCS(object):

    ARGS = None

    def __init__(self, dest):
        self.dest = os.path.abspath(dest)

    @ property
    def cmd(self):
        return self.CMD

    @ property
    def method(self):
        return self.METHOD

    @ property
    def dir(self):
        return os.path.join(self.dest, os.listdir(self.dest)[0])

    def parse_url(self, url):
        return url.split('#egg=')

    def retrieve_data(self):
        self.call_cmd([self.url])

    def check_dest(self):
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
                stdout = open(os.path.join(tempdir, 'pyg-stdout.txt'), 'w')
                stderr = open(os.path.join(tempdir, 'pyg-stderr.txt'), 'w')
                logger.info('Copying data from {0} to {1}', self.url, self.dest)
                return call_subprocess([self.cmd, self.method] + args, stdout, stderr)

    def develop(self):
        self.retrieve_data()
        if not os.path.exists(os.path.join(self.dir, 'setup.py')):
            logger.fatal('E: The repository must have a top-level setup.py file', exc=InstallationError)
        logger.info('Running setup.py develop for {0}', self.package_name)
        if call_setup(self.dir, ['develop']) != 0:
            logger.fatal('E: setup.py did not install {0}', self.package_name, exc=InstallationError)
        logger.info('{0} installed succesfully', self.package_name)

    def install(self):
        self.retrieve_data()
        Installer.from_dir(self.dir, self.package_name)