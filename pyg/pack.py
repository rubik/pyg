'''
Create Packs, like Zicbee Pack (at http://pypi.python.org/zicbee).
Inspired by zicbee-workshop's manage.py
'''

import re
import os
import sys
import glob
import shutil
import platform

from pyg.log import logger
from pyg.req import Requirement
from pyg.web import highest_version
from pyg.inst import Bundler
from pyg.core import PygError
from pyg.utils import TempDir, ZipFile, call_setup, print_output, unpack, name_from_name


PY_RUN_CODE = '''#!/usr/bin/env python
# Python executable file auto-generated by Pyg

# import pack file to extend sys.path
import {req_name}_pack
import sys

# run!
if __name__ == '__main__':
    import {mod_name}
    sys.exit({mod_name}.{callable}())
'''

PACK_PY = '''#!/usr/bin/env python
# Python file auto-generated by Pyg
# Import this file if you want to use packed modules in
# your code without unpacking the egg

import os
import sys

exists = os.path.exists
j = os.path.join
# we don't care about order
paths = set(sys.path)
paths.add(os.getcwd())

my_dir = [p for p in paths if exists(j(p, {egg!r}))]
if not my_dir:
    print "Unable to find {egg!r} file !"
    raise SystemExit()

# keep the first egg found
egg_path = os.path.join(my_dir[0], {egg!r})

# extend sys.path
sys.path.insert(0, egg_path)
'''


## Now it is still a placeholder
def _gen_executable(req_name, code):
    import_tok, func = map(str.strip, code.split(':'))
    return PY_RUN_CODE.format(
        req_name=req_name,
        mod_name=import_tok,
        callable=func,
    )


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
name = {req!r}
version = {req_version!r}
build = 1

arch = {arch}
platform = {platform!r}
osdist = None
python = {python_version!r}
packages = [
  {packages}
]
"""
    }

    def __init__(self, req, bundle_name, dest=None):
        self.req = req
        self.bundle_name = bundle_name
        self.pack_name = bundle_name
        if not self.pack_name.endswith('.zip'):
            self.pack_name = self.pack_name + '.zip'
        self.dest = dest
        self.bundled = {}
        self.entry_points = {}

    def _bundle_callback(self, req, sdist):
        sdist._name, sdist._version = req.name, req.version
        self.bundled[sdist.name.replace('-', '_')] = sdist

    def _fill_metadata(self):
        content = self.EGG_FILES['spec/depend']
        req_version = self.req.version
        try:
            if req_version is None:
                req_version = self.bundled[self.req.name].version
        except KeyError:
            pass
        if req_version is None:
            req_version = highest_version(self.req)

        self.EGG_FILES['spec/depend'] = content.format(
            req=self.req.name,
            req_version=req_version,
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

    def _mk_egg_info(self, egg_info_dir):
        ## This function returns the EGG-INFO path
        logger.info('Generating EGG-INFO...')
        with TempDir(dont_remove=True) as tempdir:
            egg_info = os.path.join(tempdir, 'EGG-INFO')
            # copy egg-info from egg_info_dir to spec/
            shutil.copytree(egg_info_dir, os.path.join(egg_info, 'spec'))

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
                                ini_file[section].update(options)
                            else:
                                ini_file[section] = options
                    result = []
                    for section in sorted(ini_file.iterkeys()):
                        result.append('[{0}]'.format(section))
                        for option, value in ini_file[section].iteritems():
                            result.append('{0} = {1}'.format(option, value))
                        result.append('\n')
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
                    mfile = os.path.join(*parts)
                    path = os.path.join(egg_info, *parts[:-1])
                    if not os.path.exists(path):
                        os.makedirs(path)
                with open(os.path.join(egg_info, mfile), 'w') as f:
                    # FIXME: this is a bit ugly
                    if mfile == 'entry_points.txt':
                        try:
                            raw = content.split('[console_scripts]')[1].split('[', 1)[0].split('\n')
                        except IndexError:
                            raw = []
                        for line in raw:
                            line = line.strip()
                            if not line:
                                continue
                            cmd, code = (x.strip() for x in line.split('='))
                            self.entry_points[cmd] = code
                    f.write(content)

            # this is for utils.ZipFile.add_to_archive: it needs the temporary
            # directory length
            tempdir_len = len(tempdir)
            return egg_info, tempdir_len

    def _gen_eggs(self, source_dir, egg_dir, egg_info_dir):
        ## Old method
        r = re.compile(r'-py\d\.\d')
        def sep_egg_info(arch_path):
            arch = os.path.basename(arch_path)
            eggname = arch[:r.search(arch).start()]
            with ZipFile(arch_path) as z:
                z.extractall(os.path.join(egg_dir, eggname))

        ## New method
        def no_egg_info(arch_path):
            with ZipFile(arch_path) as z:
                z.extractall(egg_dir)

        with TempDir() as tempdir:
            dist_dir = os.listdir(source_dir)
            dist_no = float(len(dist_dir))
            # start progress
            logger.info('\rGenerating eggs...', addn=False)
            for i, dist in enumerate(dist_dir):
                code, output = call_setup(os.path.join(source_dir, dist), ['bdist_egg', '-d', tempdir])
                if code != 0:
                    logger.fatal('Error: cannot generate egg for {0}', dist)
                    print_output(output, 'setup.py bdist_egg')
                    raise PygError('cannot generate egg for {0}'.format(dist))
                arch = os.path.join(tempdir, os.listdir(tempdir)[0])
                no_egg_info(arch)
                os.remove(arch)
                logger.info('\rGenerating eggs... [{0} - {1:.1%}]', dist, i / dist_no, addn=False)
                # copy metadata file to egg_info_dir location
                shutil.move(os.path.join(egg_dir, 'EGG-INFO'), os.path.join(egg_info_dir, dist))
            # complete the progress
            logger.info('\rGenerating eggs... 100%')

    def gen_pack(self, exclude=[], use_develop=False):
        # This is where to download all packages
        # and where to build the pack
        with TempDir() as tempdir:
            # This is where to store the egg
            with TempDir() as bundle_dir:
                logger.info('Generating the bundle...')
                b = Bundler([self.req], self.bundle_name, exclude=exclude, \
                    callback=self._bundle_callback, use_develop=use_develop)

                # we download packages without creating the bundle to build
                # eggs
                b._download_all(tempdir)
                b._clean(tempdir)

                bundle = os.path.join(bundle_dir, self.req.name) + '.egg'
                with ZipFile(bundle, mode='w') as egg:
                    # Create a new directory to store unpacked eggs
                    with TempDir() as egg_dir:
                        # where to store egg-info
                        with TempDir() as egg_info_dir:
                            # generate eggs (through distributions' setups)
                            self._gen_eggs(tempdir, egg_dir, egg_info_dir)
                            egg.add_to_archive(egg_dir, len(egg_dir))
                            # generate egg-info (merging)
                            egg_info, tl = self._mk_egg_info(egg_info_dir)
                            egg.add_to_archive(egg_info, tl)

                pack = os.path.join(tempdir, self.pack_name)
                eggname = self.req.name + '.egg'
                folder_name = '{0.name}-{0.version}'.format(self.bundled[self.req.name])
                with ZipFile(pack, mode='w') as z:
                    z.write(bundle, '/'.join([folder_name, eggname]))
                    # write executable files
                    for command_name, code in self.entry_points.iteritems():
                        z.add_executable('/'.join((folder_name, 'run_{0}.py'.format(command_name))),
                            _gen_executable(self.req.name, code)
                        )
                    # write pack file
                    z.writestr('/'.join([folder_name, '{0}_pack.py'.format(self.req.name)]),
                        PACK_PY.format(egg=eggname)
                    )
                dest = os.path.join(self.dest, self.pack_name)
                if os.path.exists(dest):
                    os.remove(dest)
                shutil.move(pack, self.dest)
