from pyg.vcs.base import VCS


__all__ = ['Git', 'Hg', 'Bzr', 'Svn']


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