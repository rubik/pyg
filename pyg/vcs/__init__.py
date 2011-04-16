from vcs import *

from pyg.log import logger


def vcs(url, dest=None):
    schemes = ('git+', 'hg+', 'bzr+', 'svn+')
    for scheme in schemes:
        if url.startswith(scheme):
           break
    else:
        logger.fatal('E: URL should start with one of these schemes:\n{0}', schemes, exc=ValueError)
    if not '#egg=' in url:
        logger.fatal('E: URL should contain `#egg=PACKAGE`', exc=ValueError)

    MAP = {
        'git': Git,
        'hg': Hg,
        'bzr': Bzr,
        'svn': Svn,
    }

    return MAP[scheme[:-1]](url, dest)