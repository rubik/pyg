from pyg.vcs.base import VCS
from pyg.utils import call_setup, print_output
from pyg.core import InstallationError
from pyg.log import logger


__all__ = ['Git', 'Hg', 'Bzr', 'Svn', 'Local']


class Git(VCS):

    CMD = 'git'
    METHOD = 'clone'

    def __init__(self, url, dest=None):
        if url.startswith('git+'):
            url = url[4:]
        self.url, self.package_name = self.parse_url(url)
        super(Git, self).__init__(dest or self.package_name)


class Hg(VCS):

    CMD = 'hg'
    METHOD = 'clone'

    def __init__(self, url, dest=None):
        if url.startswith('hg+'):
            url = url[3:]
        self.url, self.package_name = self.parse_url(url)
        super(Hg, self).__init__(dest or self.package_name)


class Bzr(VCS):

    CMD = 'bzr'
    METHOD = 'branch'

    def __init__(self, url, dest=None):
        if url.startswith('bzr+'):
            url = url[4:]
        self.url, self.package_name = self.parse_url(url)
        super(Bzr, self).__init__(dest or self.package_name)


class Svn(VCS):

    CMD = 'svn'
    METHOD = 'checkout'

    def __init__(self, url, dest=None):
        if url.startswith('svn+'):
            url = url[4:]
        self.url, self.package_name = self.parse_url(url)
        super(Svn, self).__init__(dest or self.package_name)


class Local(VCS):
    def __init__(self, url, dest=None):
        if url.startswith('dir+'):
            url = url[4:]
        self.dest, self.package_name = self.parse_url(url)

    def develop(self):
        logger.info('Running setup.py develop for {0}', self.package_name)
        code, output = call_setup(self.dest, ['develop'])
        if code != 0:
            logger.fatal('Error: setup.py develop did not install {0}', self.package_name)
            print_output(output, 'setup.py develop')
            raise InstallationError('setup.py did not install {0}'.format(self.package_name))
        logger.info('{0} installed succesfully', self.package_name)