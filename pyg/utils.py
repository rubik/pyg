import re
import os
import sys
import atexit
import shutil
import tarfile
import zipfile
import platform
import tempfile
import subprocess
import pkg_resources


from pyg.locations import PYG_LINKS, PYTHON_VERSION, under_virtualenv
from pyg.log import logger

try:
    import zlib
    COMPRESSION_LEVEL=zipfile.ZIP_DEFLATED
except ImportError:
    COMPRESSION_LEVEL=zipfile.ZIP_STORED

SETUP_PY_TEMPLATE = '''import distutils
from setuptools import setup
from setuptools.command.install import install as setuptools_install
distutils.command.install.install = setuptools_install

__file__={0!r};execfile(__file__)'''


try:
    ## subprocess.check_output has been introduced in Python 2.7
    ## Since Pyg run on Python 2.6 too, we have to reproduce it.
    check_output = subprocess.check_output
except AttributeError:
    def check_output(*popenargs, **kwargs):
        '''Borrowed from Python2.7 subprocess.py'''

        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise CalledProcessError(retcode, cmd, output=output)
        return output

class CalledProcessError(Exception):
        """This exception is raised when a process run by check_call() or
        check_output() returns a non-zero exit status.
        The exit status will be stored in the returncode attribute;
        check_output() will also store the output in the output attribute.
        """

        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output
        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (self.cmd, self.returncode)

def is_installed(req):
    '''
    Check whether the given requirement is installed or not.
    A requirement can be either a name or a name plus a version: both `pyg` and
    `pyg==0.7` are valid requirements.
    '''

    try:
        pkg_resources.get_distribution(req)
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict,
            ValueError):
        return False
    else:
        return True

def installed_distributions():
    for dist in pkg_resources.working_set:
        # Filter out Python==version, in case Pyg is executed in a virtual env
        if dist.project_name.lower() == 'python':
            continue
        yield dist

def is_windows():
    '''Return True when Pyg is running on a Windows system, False otherwise.'''

    return platform.system() == 'Windows'

def name_from_name(pkg_name):
    '''
    Get the name of a package from its egg name:

        >>> name_from_name('zicbee-mplayer-0.7-py2.7.egg')
        ('zicbee_mplayer', '-0.7-py2.7.egg')
    '''
    name, version = re.compile(r'([.\w\d_-]+)-([\d\w.]+.*)').match(pkg_name).groups()
    return "%s-%s"%(name.replace('-', '_') , version.replace('-', '_'))


    ## We could use str.split, but regex give us a better control over
    ## the strings.

def name_from_egg(eggname):
    '''
    Get the name of a package from its egg name:

        >>> name_from_egg('pyg-0.7-py2.7.egg')
        'pyg'
    '''

    ## We could use str.split, but regex give us a better control over
    ## the strings.
    egg = re.compile(r'([\w\d_]+)-.+')
    return egg.search(eggname).group(1)

def right_egg(eggname):
    '''Return True if the egg can be installed basing on the running Python version.'''

    vcode = 'py{0}'.format('.'.join(map(str, sys.version_info[:2])))
    return vcode in eggname

def version_egg(eggname):
    '''Extract Python version from an egg name.'''

    eggv = re.compile(r'py(\d\.\d)')
    return eggv.search(eggname).group(1)

def call_subprocess(args, cwd=None):
    '''
    Call subprocess with the given argument and return the tuple
    `(returncode, output)`. You can also specify the current working directory.
    '''

    try:
        output = check_output(args, stderr=subprocess.STDOUT, cwd=cwd)
    except (subprocess.CalledProcessError, CalledProcessError) as e:
        return e.returncode, e.output
    return 0, output

def call_setup(path, a):
    '''
    Call the `setup.py` file under the specified path with the given arguments.

    Note that `path` must be the directory in which the setup file is located,
    not the direct path to the file. For example, `/home/user/packages/pyg-0.7/'
    is right (assuming there is a `setup.py` file in it), while
    '/home/user/packages/pyg-0.7/setup.py` is not.
    '''

    code = SETUP_PY_TEMPLATE.format(os.path.join(path, 'setup.py'))
    args =  [sys.executable, '-c', code] + a
    # we add the --install-header option under virtualenv only if
    # we are installing
    if under_virtualenv() and 'install' in args:
        logger.debug('debug: virtualenv detected')
        headers = os.path.join(sys.prefix, 'include', 'site', 'python' + PYTHON_VERSION)
        args += ['--install-headers', headers]
    return call_subprocess(args, cwd=path)

def run_setup(path, name, global_args=[], args=[], exc=TypeError):
    '''
    Run `setup.py install` for the given setup file. `name` is the package name;
    `global_args` are the arguments to pass before the `install` command; `args`
    are the options for the `install` command and `exc` is the exception to throw
    in case of a failed installation.

    The warning for `path` is the same as `call_setup`.
    '''

    logger.info('Running setup.py install for {0}', name)
    if name == 'dreampie': # little exception to make it works
        ar = global_args + ['install'] + args
    else:
        ar = global_args + ['install', '--single-version-externally-managed',
                            '--record', os.path.join(tempfile.mkdtemp(), '.pyg-install-record')] + args
    code, output = call_setup(path, ar)
    if code != 0:
        logger.fatal('Error: setup.py did not install {0}', name)
        print_output(output, 'setup.py install')
        raise exc('setup.py did not install {0}'.format(name))

def print_output(output, cmd):
    '''Print to sys.stderr the complete output of a failed command'''

    logger.info('Complete output from command `{0}`:', cmd)
    logger.indent += 8
    for line in output.splitlines():
        logger.error(line)
    logger.indent -= 8

def name_ext(path):
    '''Like os.path.splitext(), but split off .tar too.'''

    p, e = os.path.splitext(path)
    if p.endswith('.tar'):
        e = '.tar' + e
        p = p[:-4]

    ## Little hack to support .tgz files too without adding them to
    ## pyg.web.PREFERENCES, etc.
    if e == '.tgz':
        return p, '.tar.gz'
    return p, e

def name(path):
    '''
    Return the name of a file (i.e. strip off the file extension):

        >>> name('pyg-0.7-py2.7.egg')
        'pyg-0.7-py2.7'
    '''

    return name_ext(path)[0]

def ext(path):
    '''
    Return the extension of a filename:

        >>> ext('pyg-0.7-py2.7.egg')
        '.egg'
        >>> ext('pyg-0.7.tar.gz')
        '.tar.gz'
    '''

    return name_ext(path)[1]

def unpack(path, dest=None):
    '''
    Unpack the specified archive into the same directory or a specified destination.
    '''

    path = os.path.abspath(path)
    d, n = os.path.split(path)
    e = ext(n)
    if e in ('.egg', '.zip'):
        arch = ZipFile(path)
    elif e in ('.tar', '.tar.gz', '.tar.bz2'):
        mode = 'r' if e == '.tar' else 'r:' + e.split('.')[2]
        arch = tarfile.open(path, mode=mode)
    else:
        logger.error('Unknown extension: {0}', e, exc=TypeError)
    arch.extractall(dest or d)


class TempDir(object):

    not_removed = set()

    def __init__(self, prefix='pyg-', suffix='-record', dont_remove=False):
        self.prefix = prefix
        self.suffix = suffix
        self.dont_remove = dont_remove

    def __enter__(self):
        self.tempdir = tempfile.mkdtemp(self.suffix, self.prefix)
        self.not_removed.add(self.tempdir)
        return self.tempdir

    def __exit__(self, *args):
        if not self.dont_remove:
            try:
                shutil.rmtree(self.tempdir)
            ## Experimental (remember to remove before releasing)
            except Exception as e:
                logger.verbose('Error: cannot remove temporary directory {0}: {1}', self.tempdir, e)

    @staticmethod
    @atexit.register
    def __clean_tempdir():
        to_remove = TempDir.not_removed
        if to_remove:
            logger.verbose('Cleaning temporary folders', addn=False)
            for fold in to_remove:
                if os.path.isdir(fold):
                    logger.verbose('.', addn=False)
                    try:
                        shutil.rmtree(fold)
                    except (OSError, IOError):
                        logger.verbose('\bx', addn=False)
            sys.stdout.flush()
        if logger.level <= logger.VERBOSE:
            logger.newline()


class ChDir(object):
    def __init__(self, dir):
        self.cwd = os.getcwd()
        self.dir = dir

    def __enter__(self):
        os.chdir(self.dir)
        return self.dir

    def __exit__(self, *args):
        os.chdir(self.cwd)


## No more used. Now pyg.web.ReqManager.files() uses directly
# collections.defaultdict
#
#class FileMapper(collections.defaultdict):
#    '''
#    Container for pyg.web.ReqManager, which needs it to hold files preferences.
#    '''
#
#    def __init__(self, pref):
#        self.pref = pref
#        super(FileMapper, self).__init__(list)
#
#    def __missing__(self, key):
#        if key in self.pref:
#            if key not in self:
#                self[key] = self.default_factory()
#            return self[key]
#        return self.default_factory()


## ZipFile subclass for Python < 2.7
## In Python 2.6 zipfile.ZipFile and tarfile.TarFile do not have __enter__ and
## __exit__ methods
## EDIT: Removed TarFile since it caused problems

class ZipFile(zipfile.ZipFile):
    def __init__(self, file, *args, **kwargs):
        if not 'compression' in kwargs:
            kwargs['compression'] = COMPRESSION_LEVEL
        zipfile.ZipFile.__init__(self, file, *args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def add_executable(self, filename, content):
        zi = zipfile.ZipInfo(filename)
        zi.external_attr = 0777 << 16L
        self.writestr(zi, content)

    def add_to_archive(self, dir, tempdir_len):
        for file in os.listdir(dir):
            path = os.path.join(dir, file)
            if os.path.isfile(path):
                self.write(path, path[tempdir_len:])
            elif os.path.isdir(path):
                self.add_to_archive(path, tempdir_len)

#class TarFile(tarfile.TarFile):
#    def __enter__(self):
#        return self
#
#    def __exit__(self, type, value, traceback):
#        self.close()


## This is a fake file object needed by ConfigParser.ConfigParser
## It implements only a readline() method plus an __iter__ method

class File(object):
    def __init__(self, lines):
        self._i = (l for l in lines)

    def __iter__(self):
        return self._i

    def readline(self):
        try:
            return next(self._i)
        except StopIteration:
            return ''
