import os
import site


def freeze():
    packages = []
    for packages_dir in site.getsitepackages() + [site.getusersitepackages()]:
        for dir in os.listdir(packages_dir):
            if '.egg' in dir:
                if dir.endswith('.egg-info') or dir.endswith('.egg'):
                    dir = dir.split('.egg-info')[0]
                    try:
                        name, version = dir.split('-')[:2]
                    except ValueError:
                        continue
                    packages.append('{0}=={1}'.format(name, version))
    return '\n'.join(sorted(packages)) + '\n'