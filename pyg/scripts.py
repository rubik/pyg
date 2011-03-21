'''
Script installation resources. Modified from setuptools/easy_install.py
'''


import re
import sys
import pkg_resources

SCRIPT_TEXT = '''# EASY-INSTALL-ENTRY-SCRIPT: {spec!r},{group!r},{name!r}
__requires__ = {spec!r}
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point({spec!r}, {group!r}, {name!r})()
    )'''

if sys.version_info <= (3,):
    def isascii(s):
        try:
            unicode(s, 'ascii')
            return True
        except UnicodeError:
            return False
else:
    def isascii(s):
        try:
            s.encode('ascii')
            return True
        except UnicodeError:
            return False

def nt_quote_arg(arg):
    result = []
    needquote = False
    nb = 0

    needquote = (" " in arg) or ("\t" in arg)
    if needquote:
        result.append('"')

    for c in arg:
        if c == '\\':
            nb += 1
        elif c == '"':
            # double preceding backslashes, then add a \"
            result.append('\\' * (nb * 2) + '\\"')
            nb = 0
        else:
            if nb:
                result.append('\\' * nb)
                nb = 0
            result.append(c)

    if nb:
        result.append('\\' * nb)
    if needquote:
        result.append('\\' * nb)    # double the trailing backslashes
        result.append('"')
    return ''.join(result)

def get_script_header(script_text, executable=sys.executable):
    first_line_re = re.compile('^#!.*python[0-9.]*([ \t].*)?$')
    first = (script_text + '\n').splitlines()[0]
    match = first_line_re.match(first)
    options = ''
    if match:
        options = match.group(1) or ''
        if options:
            options = ' ' + options
    executable = nt_quote_arg(executable)
    hdr = "#!{0}{1}\n".format(executable, options)
    if not isascii(hdr):
        # Non-ascii path to sys.executable, use -x to prevent warnings
        if options:
            if options.strip().startswith('-'):
                options = ' -x' + options.strip()[1:]
            # else: punt, we can't do it, let the warning happen anyway
        else:
            options = ' -x'
    hdr = "#!{0}{1}\n".format(executable, options)
    return hdr

def script_args(dist):
    spec = str(dist.as_requirement())
    header = get_script_header("", sys.executable)
    for group in 'console_scripts', 'gui_scripts':
        for name, ep in dist.get_entry_map(group).items():
            script_text = SCRIPT_TEXT.format(**locals())
            if sys.platform == 'win32':
                # On Windows/wininst, add a .py extension and an .exe launcher
                if group == 'gui_scripts':
                    ext, launcher = '-script.pyw', 'gui.exe'
                    new_header = re.sub('(?i)python.exe', 'pythonw.exe', header)
                else:
                    ext, launcher = '-script.py', 'cli.exe'
                    new_header = re.sub('(?i)pythonw.exe', 'python.exe', header)

                if os.path.exists(new_header[2:-1]):
                    hdr = new_header
                else:
                    hdr = header
                yield (name + ext, hdr + script_text, 't')
                yield (
                    name + '.exe', pkg_resources.resource_string('setuptools', launcher),
                    'b' # write in binary mode
                )
            else:
                # On other platforms, we assume the right thing to do is to
                # just write the stub with no extension.
                yield (name, header + script_text, '')