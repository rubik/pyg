from lettuce import *
import os
import re
import shutil
import tempfile
import itertools
from glob import glob
from subprocess import Popen, PIPE, call


VENV_DIR = os.getenv('KEEPENV', None) or tempfile.mkdtemp(prefix='pyg_env_')

ENVIRONMENTS = { 'standard': os.path.join(VENV_DIR, 'standard') }

@before.each_feature
def remove_std_packages(*a):
    for env, path in ENVIRONMENTS.iteritems():
        try:
            call([os.path.join(path, 'bin', 'pyg'),
                'remove',
                '-y',
                'bottle',
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
    if 'KEEPENV' in os.environ and os.path.exists(VENV_DIR):
        return

    try:
        shutil.rmtree(VENV_DIR)
    except OSError, e:
        print "Unable to remove %r : %r"%(VENV_DIR, e)
    os.mkdir(VENV_DIR)

@after.all
def destroy_env(*a):
    """ Ensure VENV_DIR folder is destroyed, set KEEPENV=/some/folder to disable. """
    if 'KEEPENV' in os.environ:
        print "Env. path: %s" % VENV_DIR
    else:
        shutil.rmtree(VENV_DIR)

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
            args = ['--python', 'python'+py_version]
        else:
            args = []

        call(['virtualenv'] + args + ['--no-site-packages', world.env_path])

    # Install pyg if not found
    if not os.path.exists(os.path.join(world.env_path, 'bin', 'pyg')):
        dn = os.path.dirname
        pyg_dir = dn(dn(dn(__file__))) + '/'
        os.chdir(pyg_dir)

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

@step('I execute +(.*)')
def i_execute(step, cmd):
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
