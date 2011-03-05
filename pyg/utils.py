import shutil
import tempfile
import pkg_resources


def is_installed(req):
    try:
        pkg_resources.get_distribution(req)
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict, ValueError):
        return False
    else:
        return True


class TempDir(object):
    def __init__(self, prefix='pyg-', suffix='-record'):
        self.prefix = prefix
        self.suffix = suffix

    def __enter__(self):
        self.tempdir = tempfile.mkdtemp(self.suffix, self.prefix)
        return self.tempdir
    
    def __exit__(self, *args):
        shutil.rmtree(self.tempdir)