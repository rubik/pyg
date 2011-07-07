'''
Create Packs, like Zicbee Pack (at http://pypi.python.org/zicbee).
Inspired by zicbee-workshop's manage.py
'''

import os
import sys
import glob
import shutil
import platform

from pyg.req import Requirement
from pyg.inst import Bundler
from pyg.utils import TempDir, ZipFile


class Packer(object):

    EMPTY, INI, CAT, SCAT, MERGE = range(5)
    REQ = 42

    EGG_FILES = {
        'dependency_links.txt': MERGE,
        'entry_points.txt': INI,
        'not-zip-safe': EMPTY,
        'PKG-INFO': REQ,
        'requires.txt': EMPTY,
        'SOURCES.txt': SCAT,
        'top_level.txt': SCAT,
        'spec/depend': """metadata_version = '1.1'
name = '{req}'
version = '{req_version}'
build = 1

arch = {arch}
platform = '{platform}'
osdist = None
python = '{python_version}'
packages = [
  {packages}
]
            """
    }

    def __init__(self, req, bundle_name, dest=None):
        self.req = req
        self.bundle_name = bundle_name
        self.dest = dest
        self.bundled = {}

    def _bundle_callback(self, sdist):
        self.bundled[sdist.name] = sdist

    def _fill_metadata(self):
        content = self.EGG_FILES['spec/depend']
        self.EGG_FILES['spec/depend'] = content.format(
            req=self.req.name,
            req_version=self.req.version,
            arch=platform.machine(),
            platform=sys.platform,
            python_version='.'.join(map(str, sys.version_info[:2])),
            packages=',\n  '.join('{0.name} {0.version}'.format(dist) for dist in self.bundled.values())
        )

    def _safe_readlines(self, dist, filename):
        try:
            return dist.file(filename)
        except KeyError:
            return {}

    def _mk_egg_info(self):
        ## This function should return the EGG-INFO path

        with TempDir(dont_remove=True) as tempdir:
            egg_info = os.path.join(tempdir, 'EGG-INFO')
            os.mkdir(egg_info)
            self._fill_metadata()
            for mfile, data in self.EGG_FILES.iteritems():
                deps = dict((name, self._safe_readlines(dist, mfile)) for name, dist in self.bundled.iteritems())
                if data == self.EMPTY:
                    content = ''
                elif data == self.INI:
                    ini_file = {}
                    for dep, content in deps.iteritems():
                        for section, options in content.iteritems():
                            if section in ini_file:
                                ini_file[section].update(content)
                            else:
                                ini_file[section] = content
                    result = []
                    for section in sorted(ini_file.iterkeys()):
                        for option, value in ini_file[section].iteritems():
                            result.append('{0} = {1}'.format(option, value))
                    content = '\n'.join(result)
                elif data in (self.CAT, self.SCAT):
                    lines = []
                    for dep, content in deps.iteritems():
                        lines.extend(content)
                    if data == self.SCAT:
                        lines.sort()
                    content = '\n'.join(lines)
                elif data == self.MERGE:
                    d = set()
                    for dep, content in deps.iteritems():
                        d.update(content)
                    content = '\n'.join(sorted(d))
                elif data == self.REQ:
                    content = '\n'.join('{0}: {1}'.format(opt, val) \
                        for opt, val in self._safe_readlines(self.bundled[self.req.name], mfile).iteritems())
                else:
                    content = data

                if '/' in mfile:
                    # Make it platform-indipendent
                    parts = mfile.split('/')
                    mfile = os.path.join(*mfile.split('/'))
                    os.makedirs(os.path.join(egg_info, *parts[:-1]))
                with open(os.path.join(egg_info, mfile), 'w') as f:
                    f.write(content)

            return egg_info

    def gen_pack(self):
        with TempDir() as tempdir:
            b = Bundler([self.req], self.bundle_name, dest=tempdir, callback=self._bundle_callback)
            b.bundle(include_manifest=False, build_dir=False, add_func=self._mk_egg_info)

            bundle = os.path.join(b.destination, b.bundle_name)
            packname = self.req.name + '.pypack'
            pack = os.path.join(tempdir, packname)
            with ZipFile(pack, mode='w') as z:
                z.write(bundle, self.req.name + '.egg')
            # XXX: Add executable files
            dest = os.path.join(self.dest, packname)
            if os.path.exists(dest):
                os.remove(dest)
            shutil.move(pack, self.dest)


if __name__ == '__main__':
    p= Packer(Requirement('pyg'), 'pyg_test_pack', os.path.expanduser('~'))
    p.gen_pack()