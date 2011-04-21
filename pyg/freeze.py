import pkg_resources

from pkgtools.pypi import PyPIXmlRpc
from pyg.web import WebManager
from pyg.utils import is_installed


def freeze():
    packages = []
    for dist in pkg_resources.working_set:
        packages.append('{0.project_name}=={0.version}'.format(dist))
    return sorted(packages)

def list_releases(name):
    name = name[:-1] + '_' if name.endswith('-') else name
    res = []
    versions = PyPIXmlRpc().package_releases(name, True)
    if not versions:
        versions = map(str, sorted(WebManager.versions_from_html(name), reverse=True))
    for v in versions:
        if is_installed('{0}=={1}'.format(name, v)):
            res.append((v, True))
        else:
            res.append((v, False))
    return res