import pkg_resources


def is_installed(req):
    try:
        pkg_resources.get_distribution(req)
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict, ValueError):
        return False
    else:
        return True