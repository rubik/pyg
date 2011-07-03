from lettuce import *
from subprocess import Popen, PIPE

@step('I use "(.*)" environment')
def given_i_use_venv(step, env_name):
    world.env_name = env_name

@step('I execute +(.*)')
def i_execute(step, cmd):
    world.proc = Popen(cmd.split(), stdin=PIPE, stdout=PIPE, stderr=PIPE)

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
