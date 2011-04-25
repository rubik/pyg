import os
import sys
import cmd
import shutil
import difflib

from pyg.parser.parser import init_parser
from pyg.types import PygError, InstallationError, AlreadyInstalled


__all__ = ['PygShell']


SUPPORTED_COMMANDS = ['install', 'uninstall', 'rm', 'list', 'freeze', 'link',
                      'unlink', 'search', 'download', 'check', 'update', 'bundle']
ADDITIONAL_COMMANDS = ['cd', 'pwd', 'ls']
HELP = '''Supported commands:
===================

{0}


Additional commands:
====================

{1}
'''


def command_hook(attr):
    def wrapper(*args, **kwargs):
        if attr == 'EOF':
            print '\n'
            return True
        print '*** Unknown command: {0}'.format(attr)
        close = difflib.get_close_matches(attr, SUPPORTED_COMMANDS, n=1, cutoff=0.5)
        if close:
            print 'Did you mean this?\n\t{0}'.format(close[0])
    return wrapper

def command(parser, cmd_name):
    def inner(args):
        try:
            return parser.dispatch([cmd_name] + args.split())
        except (SystemExit, AlreadyInstalled, PygError):
            pass
        except Exception as e:
            print e
    return inner


class PygShell(cmd.Cmd, object):
    def __init__(self, *args, **kwargs):
        self.startdir = os.getcwd()
        self.prompt = 'pyg:{0}$ '.format(self.startdir)
        self.parser = init_parser(__import__('pyg').__version__)
        super(PygShell, self).__init__(*args, **kwargs)

    def __getattr__(self, attr):
        if not attr.startswith('do_') or attr in ADDITIONAL_COMMANDS:
            return object.__getattr__(self, attr)
        attr = attr[3:]
        if not attr in SUPPORTED_COMMANDS:
            return command_hook(attr)
        return command(self.parser, attr)

    def do_help(self, line):
        print HELP.format('  '.join(SUPPORTED_COMMANDS), '   '.join(ADDITIONAL_COMMANDS))

    def do_exit(self, line):
        return self.do_EOF()

    def do_cd(self, line):
        paths = line.split()
        if not paths:
            return self.do_cd(self.startdir)
        try:
            path = os.path.abspath(paths[0])
            os.chdir(path)
        except OSError as e:
            print 'cd: {0}'.format(e.strerror)
        else:
            self.prompt = 'pyg:{0}$ '.format(path)

    def do_pwd(self, line):
        print os.getcwd()

    #def do_rm(self, line):
    #    if not line.split():
    #        print '*** Error: rm must have an argument'
    #        return
    #    path = line.split()[0]
    #    try:
    #        if os.path.isdir(path):
    #            shutil.rmtree(path)
    #        else:
    #            os.remove(path)
    #    except OSError as e:
    #        print 'rm: {0}: {1}'.format(e.strerror, path)

    def do_ls(self, line):
        args = line.split()
        path = args[0] if args else os.getcwd()
        ls = os.listdir(path)
        if not '-a' in args and not '--all' in args:
            ls = [p for p in ls if not p.startswith('.')]
        print '  '.join(sorted(ls))