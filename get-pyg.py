import os
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


def splitext(path):
    name, e = os.path.splitext(path)
    if name.endswith('.tar'):
        return name[:-4], '.tar' + e
    return name, e

def unpack(path):
    filename = os.path.basename(path)
    ext = splitext(filename)
    if ext in ('.tar', '.tar.gz', '.tar.bz2'):
        if ext == '.tar':
            mode = 'r'
        else:
            mode = 'r:{0}'.format(ext.split('.')[-1])
        archive = tarfile.open(path, mode=mode)
    elif ext == '.zip':
        archive = zipfile.open(path)
    else:
        raise TypeError('Unknown file-type: {0}'.format(ext))
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
    path = urllib.urlretrieve(url)[0]
    path = unpack(path)
    setup_py = os.path.join(path, 'setup.py')
    subprocess.check_call(['python', setup_py, 'install'])