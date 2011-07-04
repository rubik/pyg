import os
from lettuce import *
from subprocess import Popen, PIPE, call

VENV_DIR="/tmp/test_envs"

@before.all
def init_env(*a):
    """ Ensure VENV_DIR folder is empty """
    import shutil
    try:
        shutil.rmtree(VENV_DIR)
    except OSError:
        pass
    os.mkdir(VENV_DIR)

@step('I use "(.*)" environment')
def given_i_use_venv(step, env_name):
    world.env_name = env_name
    world.env_path = os.path.join(VENV_DIR, env_name)

    # Create Venv if it can't be found
    if not os.path.exists(world.env_path):
        call(['virtualenv', '--no-site-packages', world.env_path])

    # Install pyg if not found
    if not os.path.exists(os.path.join(world.env_path, 'bin', 'pyg')):

        pyg_dir = os.path.dirname(os.path.dirname(__file__))
        call([ os.path.join(world.env_path, 'bin', 'python'),
            os.path.join(pyg_dir, 'setup.py'),
            'install'
            ])

@step('I execute +(.*)')
def i_execute(step, cmd):
    world.proc = Popen(os.path.join(world.env_path, 'bin', cmd),
     stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

@step('the return code is (\d+)')
def the_return_code_is(step, code):
    if int(code) != world.proc.wait():
        world.stdout, world.stderr = world.proc.communicate()
        out_desc = "OUT:\n%sERR:\n%s\n-EOF-\n"%(world.stdout, world.stderr)
        raise AssertionError('Invalid code, expected %s, got %d\n%s'%(code, world.proc.returncode, out_desc))

@step('the stdout contains (\s+)')
def the_stdout_is(step, text):
    if text not in world.stdout:
        raise AssertionError('Could not find string %r, got:\n%s\nEOF'%(text, world.stdout))

@step('the stderr contains (\s+)')
def the_stderr_is(step, text):
    if text not in world.stderr:
        raise AssertionError('Could not find string %r, got:\n%s\nEOF'%(text, world.stderr))
