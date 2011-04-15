from pyg.vcs import VCS


class Git(VCS):

    CMD = 'git'
    METHOD = 'clone'

    def __init__(self, url, dest=None):
        if url.startswith('git+'):
            url = url[4:]
        self.url, self.package_name = self.parse_url(url)
        super(Git, self).__init__(dest or self.package_name)