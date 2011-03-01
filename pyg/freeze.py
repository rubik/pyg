import os
import site


def freeze():
    packages = []
    for packages_dir in site.getsitepackages():
        for dir in os.listdir(packages_dir):
            if dir.endswith('.egg'):
                name, version = dir.split('-')[:2]
                packages.append('{0}=={1}'.format(name, version))
    return '\n'.join(packages)