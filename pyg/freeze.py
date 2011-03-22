import os
import pkg_resources


def freeze():
    packages = []
    for dist in pkg_resources.working_set:
        packages.append('{0.project_name}=={0.version}'.format(dist))
    return sorted(packages)