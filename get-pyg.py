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


URL = 'http://pypi.python.org/pypi/pyg/json'


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

def get_url():
    data = urllib2.urlopen(URL).read()
    json_data = json.loads(data)
    installable = (release for release in json_data['urls'] if release['packagetype'] == 'sdist')
    return min(installable, key=lambda item: item['size'])['url']

def install():
    url = get_url()
    log('Retrieving archive...')
    path = urllib.urlretrieve(url)[0]
    log('Unpacking archive...')
    path = unpack(path)
    setup_py = os.path.join(path, 'setup.py')
    python = 'python{0}.{1}'.format(*sys.version_info[:2])
    try:
        log('Running setup.py install...')
        subprocess.check_call([python, setup_py, 'install'], cwd=path)
    except subprocess.CalledProcessError as e:
        log('Installation failed. Installation command returned non-zero ' \
            'exit status: ' + str(e.returncode) + '\n')


if __name__ == '__main__':
    install()