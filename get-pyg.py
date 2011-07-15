#! /usr/bin/env python

import os
import sys
import urllib
import urllib2
import tarfile
import zipfile
import tempfile
import subprocess

try:
    import simplejson as json
except ImportError:
    import json


URL = 'http://pypi.python.org/pypi/{0}/json'


def log(msg):
    return sys.stdout.write(msg + '\n')

def unpack(path):
    if tarfile.is_tarfile(path):
        archive = tarfile.open(path)
    elif zipfile.is_zipfile(path):
        archive = zipfile.open(path)
    else:
        raise TypeError('Unknown file-type: {0}'.format(path))
    tempdir = tempfile.mkdtemp()
    archive.extractall(tempdir)
    return os.path.join(tempdir, os.listdir(tempdir)[0])

def get_url(url):
    data = urllib2.urlopen(url).read()
    json_data = json.loads(data)
    installable = (release for release in json_data['urls'] if release['packagetype'] == 'sdist')
    return min(installable, key=lambda item: item['size'])['url']


def install(pkg):
    log('Installing {0}'.format(pkg))
    if '--dev' in sys.argv and pkg == 'pyg':
        url = 'https://github.com/rubik/pyg/tarball/master'
    else:
        url = get_url(URL.format(pkg))
    log('Retrieving archive from {0}'.format(url))
    path = urllib.urlretrieve(url)[0]
    log('Unpacking archive...')
    path = unpack(path)
    setup_py = os.path.join(path, 'setup.py')
    try:
        log('Running setup.py install...')
        subprocess.check_call([sys.executable, setup_py, 'install'], cwd=path)
    except subprocess.CalledProcessError as e:
        log('Installation failed. Installation command returned non-zero ' \
            'exit status: ' + str(e.returncode) + '\n')

def main():
    try:
        import setuptools
    except ImportError:
        install('setuptools')
    install('pyg')


if __name__ == '__main__':
    main()