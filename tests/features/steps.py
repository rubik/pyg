from lettuce import *
import os
import re
import sys
import json
import shutil
import tempfile
import itertools
from glob import glob
from subprocess import Popen, PIPE, call, check_call
# FIXME: Can we do this?
from pyg.utils import check_output, CalledProcessError # for Python 2.6

USE_PROXY = False

VENV_DIR = os.getenv('KEEPENV', None) or tempfile.mkdtemp(prefix='pyg_env_')

if VENV_DIR.isdigit() or VENV_DIR.lower() in ('true', 'yes'):
    VENV_DIR = tempfile.mkdtemp(prefix='pyg_env_')

try:
    ENVIRONMENTS = dict((p, os.path.join(VENV_DIR, p))
        for p in os.listdir(VENV_DIR)
        if os.path.isdir(os.path.join(VENV_DIR, p))
    )
except OSError:
    ENVIRONMENTS = {}

def refresh_json():
    if 'KEEPENV' in os.environ:
        info_path = os.path.join(VENV_DIR, 'infos.js')
        try:
            d = json.load(open(info_path))
            d.update(ENVIRONMENTS)
        except (OSError, IOError), e:
            d = ENVIRONMENTS
            print "Warn: can't read js file: %r"%e
        print "env: ", d
        json.dump(d, open(info_path, 'w'))

@before.each_feature
def remove_std_packages(*a):
    for env, path in ENVIRONMENTS.iteritems():
        try:
            call([os.path.join(path, 'bin', 'pyg'),
                'remove',
                '-y',
                'bottle',
                'buzhug',
                'mercurial',
                'lk',
                'grin',
                'hg-git',
                'gevent'])
        except OSError:
            pass

@before.all
def init_env(*a):
    """ Ensure VENV_DIR folder exists and is empty (unless KEEPENV is used) """
    tmp_folder = '/tmp'
    world.temp_content = set(os.listdir(tmp_folder))

    if 'KEEPENV' in os.environ and os.path.exists(VENV_DIR):
        return
    try:
        print "removing old venv..."
        shutil.rmtree(VENV_DIR)
    except OSError, e:
        print "Unable to remove %r : %r"%(VENV_DIR, e)
    os.mkdir(VENV_DIR)

@after.all
def destroy_env(*a):
    """ Ensure VENV_DIR folder is destroyed, set KEEPENV=/some/folder to disable. """
    tmp_folder = '/tmp'
    current_temp_content = set(os.listdir(tmp_folder))
    if current_temp_content != world.temp_content:
        print "WARNING: Stale temporary files:"
        for name in current_temp_content.difference(world.temp_content):
            print "* ", name

    if 'KEEPENV' in os.environ:
        print "Env. path: %s" % VENV_DIR
    else:
        print "removing venv..."
        shutil.rmtree(VENV_DIR)
        ENVIRONMENTS.clear()
    refresh_json()

@step('I use "(.*)" temporary folder')
def given_i_use_tmp_folder(step, folder_name):
    p = os.path.join(VENV_DIR, folder_name)
    try:
        os.mkdir(p)
    except:
        pass

    os.chdir(p)
    world.cur_dir = folder_name

@step('I remove "(.*)"')
def i_remove_xxx(step, fname):
    if os.path.isdir(fname):
        shutil.rmtree(fname)
    elif os.path.exists(fname):
        os.unlink(fname)

@step('there is (\d+) files')
def there_is_xx_files(self, num):
    current = len(os.listdir(os.path.curdir))-2
    if current != int(num):
        raise AssertionError('Wrong number of files in %s, expected: %s, got: %s.'%(
            world.cur_dir,
            num,
            current))

@step('I use "(.*)" environment')
def given_i_use_venv(step, env_name):
    world.env_path = os.path.join(VENV_DIR, env_name)
    # build python version from environment name
    py_version = re.compile('.*?(\d+\.?\d*)$').match(env_name)

    if py_version:
        py_version = py_version.groups()[0]

    # Create Venv if it can't be found
    if not os.path.exists(world.env_path):
        ENVIRONMENTS[env_name] = world.env_path
        if py_version:
            args = ['--python', 'python' + py_version]
        else:
            args = []

        print "Installing venv..."
        call(['virtualenv'] + args + ['--no-site-packages', world.env_path])

    # Install pyg if not found
    if not os.path.exists(os.path.join(world.env_path, 'bin', 'pyg')):
        print "Copying pyg..."
        dn = os.path.dirname
        pyg_dir = os.path.abspath(dn(dn(dn(__file__))) + '/')
        os.chdir(pyg_dir)
        install_dir = os.path.abspath(os.path.join(world.env_path, 'pyg-current'))
        if install_dir.startswith(pyg_dir):
            sys.exit("Can't use a virtual environment inside sources folder !")
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        shutil.copytree(os.path.curdir, install_dir)
        os.chdir(install_dir)
        print "Installing pyg..."
        call('. %s ; python %s develop' % (
         os.path.join(world.env_path, 'bin', 'activate'),
         os.path.join(pyg_dir, 'setup.py'),
        ), shell=True)

    os.chdir(world.env_path)

def wait_and_set():
    if world.proc:
        world.stdout, world.stderr = world.proc.communicate()
        world.returncode = world.proc.returncode
        world.proc = None
    return (world.returncode, world.stdout, world.stderr)

@step('I execute pyg\s+(.*)')
def i_execute(step, cmd):
    if ' ' in cmd:
        cmd, args = (x.strip() for x in cmd.split(None, 1))
    else:
        args = ''

    if cmd != 'help' and not cmd.startswith('-'):
        if USE_PROXY and cmd in (
                "install",
                "bundle",
                "download",
                "pack",
                "search",
                "list",
                "update"):
            cmd = "pyg -d %s -i http://localhost:8080 %s"%(cmd, args)
        else:
            cmd = "pyg -d %s %s"%(cmd, args)
    else:
        cmd = "pyg %s %s"%(cmd, args)

    prefixed_cmd = os.path.join(world.env_path, 'bin', cmd)
    world.last_cmd = prefixed_cmd
    world.proc = Popen(prefixed_cmd,
     shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

@step('no trace of \s*(\w+).*')
def no_trace_of(step, what):
    matches = glob(os.path.join(world.env_path, 'lib', 'python*', 'site-packages', what))
    if 0 != len(matches):
        pfx_len = 1 + len(glob(os.path.join(world.env_path, 'lib', 'python*', 'site-packages'))[0])
        raise AssertionError('Found stale files : %s' % ', '.join(x[pfx_len:] for x in matches))

@step('the return code is (\d+)')
def the_return_code_is(step, given_code):
    code, out, err = wait_and_set()
    if int(given_code) != code:
        out_desc = "cmd: %s\nstdout:\n%s\nstderr:\n%s\n-EOF-\n" % (
         world.last_cmd, out, err)
        raise AssertionError('Invalid code, got %s, expected %s\n%s' % (
         code, given_code, out_desc))

@step('(?P<pkg>pyg_testsource|pyg_testegg) is installed and works properly')
def is_installed_and_works_properly(step, pkg):
    bin = os.path.join(world.env_path, 'bin')
    try:
        python_bin = os.path.join(bin, 'python')
        check_call([python_bin, '-c', 'import {0};assert {0}.PKG_TYPE=={0!r}'.format(pkg)])
    except CalledProcessError:
        raise AssertionError('Cannot import %s, package not installed correctly' % (pkg))
    # test command line output
    output = check_output([os.path.join(bin, pkg)])
    assert output == 'Pyg test', 'Expected %s, got %s' % (pkg, output)

@step('(?P<num>\d+|many|all|one|a single|no)\s*(?P<what>\w+)?\s*lines? matche?s?\s+(?P<expression>.*)')
def x_line_matches(step, num, expression, what):
    # prepare arguments
    if num in ('one', 'a single'):
        num = 1
    if not what:
        what = 'stdout'

    # get result & count matching lines
    cnt = itertools.count()
    total = itertools.count()
    code, out, err = wait_and_set()
    r = re.compile(expression)
    for line in (err if 'err' in what else out).split('\n'):
        if not line.strip():
            continue

        if r.match(line):
            cnt.next()
        total.next()

    # handle result

    cnt = cnt.next()
    total = total.next()

    err_desc = "\ncmd:%s\nINFO:\nExpect %s \"%s\" (%s) \nstdout: %s\nstderr: %s\n" % (
     world.last_cmd, num, expression, what, out, err)

    if num == 'all':
        if cnt != total:
          if abs(cnt-total) < 2:
              print "Warning ! Log file tolerance, got %s instead of %s"%(cnt, total)
          else:
            raise AssertionError('Some line mismatch!'+err_desc)
    elif num == 'no':
        if cnt:
          raise AssertionError('Got matches!'+err_desc)
    elif num == 'many':
        if cnt == 0:
            raise AssertionError('No match!'+err_desc)
        elif cnt == 1:
            raise AssertionError('Single match!'+err_desc)
    elif cnt != int(num):
        if cnt == 0:
            raise AssertionError('No match!'+err_desc)
        else:
            raise AssertionError('Expected %s matches, got %d%s' % (num, cnt, err_desc))
