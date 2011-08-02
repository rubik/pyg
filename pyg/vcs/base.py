import os
import sys
import shutil
import subprocess

from pyg.utils import call_subprocess, call_setup, print_output
from pyg.inst import Installer
from pyg.core import InstallationError, PygError
from pyg.log import logger


class VCS(object):

    ARGS = None

    def __init__(self, dest):
        self.dest = os.path.abspath(dest)

        ## Check command line programs existence (git, hg, bzr, etc.) to avoid
        ## strange errors.
        try:
            subprocess.check_call([self.cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (OSError, subprocess.CalledProcessError) as e:
            # git returns 1 when it displays help
            if not (self.cmd == 'git' and e.returncode == 1):
                logger.fatal('Error: {0!r} command not found. Please make sure you ' \
                    'have installed required vcs', self.cmd, exc=PygError)

    def __repr__(self):
        return '<{0}[{1}] object at {2}>'.format(self.__class__.__name__,
                                                 self.package_name,
                                                 id(self))

    @property
    def cmd(self):
        return self.CMD

    @property
    def method(self):
        return self.METHOD

    @property
    def dir(self):
        try:
            return os.path.join(self.dest, os.listdir(self.dest)[0])
        except OSError:
            return None

    def parse_url(self, url):
        if not '#egg=' in url:
            raise ValueError('You must specify #egg=PACKAGE')
        return url.split('#egg=')

    def develop(self):
        self.retrieve_data()
        if not os.path.exists(os.path.join(self.dir, 'setup.py')):
            logger.fatal('Error: The repository must have a top-level setup.py file', exc=InstallationError)
        logger.info('Running setup.py develop for {0}', self.package_name)
        code, output = call_setup(self.dir, ['develop'])
        if code != 0:
            logger.fatal('Error: setup.py develop did not install {0}', self.package_name)
            print_output(output, 'setup.py develop')
            raise InstallationError('setup.py did not install {0}'.format(self.package_name))
        logger.info('{0} installed succesfully', self.package_name)

    def install(self):
        self.retrieve_data()
        Installer.from_dir(self.dir, self.package_name)

    def retrieve_data(self):
        code, output = self.call_cmd([self.url])
        if code != 0:
            logger.fatal('Error: Cannot retrieve data')
            print_output(output, '{0} {1}'.format(self.cmd, self.method))
            logger.raise_last(InstallationError)

    def call_cmd(self, args):
        ## Ensure that the destination directory exists
        self.check_dest()
        if self.ARGS is not None:
            args = self.ARGS + args
        logger.info('Copying data from {0} to {1}', self.url, self.dest)
        return call_subprocess([self.cmd, self.method] + args, cwd=self.dest)

    def check_dest(self):
        ## If the target directory is empty we don't have to worry
        try:
            if not os.listdir(self.dest):
                return
        ## If self.dest does not exist we leave it as it is, because it will be
        ## created by the `else` clause (below)
        except OSError:
            pass
        if os.path.exists(self.dest):
            txt = 'The destination already exists: {0}\nWhat do you want to do ?'.format(self.dest)
            u = logger.ask(txt, choices={'destroy': 'd', 'backup': 'b', 'exit': 'x'})
            if u == 'd':
                logger.info('Removing {0}...', self.dest)
                shutil.rmtree(self.dest)
                os.makedirs(self.dest)
            elif u == 'b':
                dst = os.path.join(os.path.dirname(self.dest),
                                                    self.dest + '-pyg-backup')
                logger.info('Moving {0} to {1}', self.dest, dst)
                shutil.move(self.dest, dst)
                os.makedirs(self.dest)
            elif u == 'x':
                logger.info('Exiting...')
                sys.exit(0)
        else:
            os.makedirs(self.dest)