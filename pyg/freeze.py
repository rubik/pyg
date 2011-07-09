import sys
import distutils
import pkg_resources

from pyg import __version__
from pyg.req import Requirement
from pyg.web import get_versions
from pyg.utils import is_installed


__all__ = ['freeze', 'list_releases', 'site_info']


def freeze():
    '''Freeze the current environment (i.e. all installed packages).'''

    packages = []
    for dist in pkg_resources.working_set:
        packages.append('{0.project_name}=={0.version}'.format(dist))
    return sorted(packages)

def list_releases(name):
    '''List all releases for the given requirement.'''

    name = name[:-1] + '_' if name.endswith('-') else name
    res = []
    for v in get_versions(Requirement(name)):
        v = str(v)
        if is_installed('{0}=={1}'.format(name, v)):
            res.append((v, True))
        else:
            res.append((v, False))
    return res

def site_info():
    '''Return some site information'''

    template = '''# Python version: {py_version!r}
# Python version info: {py_version_info!r}
# Python Prefix: {prefix!r}
# Platform: {platform!r}
# Pyg version: {pyg_version!r}

'''

    return template.format(
        py_version=sys.version,
        py_version_info='.'.join(str(v) for v in sys.version_info),
        platform=distutils.util.get_platform(),
        prefix=sys.prefix,
        pyg_version=__version__
    )