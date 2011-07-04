from lettuce import *
import os
import re
import shutil
import tempfile
from subprocess import Popen, PIPE, call

VENV_DIR = tempfile.mkdtemp(prefix='pyg_env_')

@before.all
def init_env(*a):
    """ Ensure VENV_DIR folder exists and is empty """
    try:
        shutil.rmtree(VENV_DIR)
    except OSError:
        pass
    os.mkdir(VENV_DIR)

@after.all
def destroy_env(*a):
    """ Ensure VENV_DIR folder is destroyed, set KEEPENV to disable. """

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
        if py_version:
            args = ['--python', 'python'+py_version]
        else:
            args = []

        call(['virtualenv'] + args + ['--no-site-packages', world.env_path])

    # Install pyg if not found
    if not os.path.exists(os.path.join(world.env_path, 'bin', 'pyg')):
        dn = os.path.dirname
        pyg_dir = dn(dn(dn(__file__)))+'/'
        os.chdir(pyg_dir)

        call('. %s ; python %s install' % (
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
    world.proc = Popen(prefixed_cmd,
     shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)

@step('the return code is (\d+)')
def the_return_code_is(step, given_code):
    code, out, err = wait_and_set()
    if int(given_code) != code:
        out_desc = "OUT:\n%sERR:\n%s\n-EOF-\n" % (out, err)
        raise AssertionError('Invalid code, expected %s, got %d\n%s' % (code, code, out_desc))

@step('the stdout contains\s+(.*)')
def the_stdout_contains(step, text):
    code, out, err = wait_and_set()
    if text not in out:
        raise AssertionError('Could not find string %r, got:\n%s\nEOF' % (text, out))

@step('the stderr contains\s+(.*)')
def the_stderr_is(step, text):
    code, out, err = wait_and_set()
    if text not in err:
        raise AssertionError('Could not find string %r, got:\n%s\nEOF' % (text, world.stderr))
