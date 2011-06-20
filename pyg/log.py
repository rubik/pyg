import sys
import logging


__all__ = ['logger']

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=False)
    colors = {
        'good'   : Fore.GREEN,
        'bad'    : Fore.RED,
        'vgood'  : Fore.GREEN + Style.BRIGHT,
        'vbad'   : Fore.RED + Style.BRIGHT,

        'std'    : '', # Do not color "standard" text
        'warn'   : Fore.YELLOW + Style.BRIGHT,
        'reset'  : Style.RESET_ALL,
    }
except ImportError:
    colors = {
        'good'   : '',
        'bad'    : '',
        'vgood'  : '',
        'vbad'   : '',

        'std'    : '',
        'warn'   : '',
        'reset'  : '',
    }


class Logger(object):

    VERBOSE = logging.DEBUG - 1
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    ## This attribute is set to True when the user does not want colors
    ## by __init__.py
    _NO_COLORS = False

    def __init__(self,level=None):
        self.indent = 0
        self.level = level or Logger.INFO
        self._stack = []
        self.enabled = True

    def disable_colors(self):
        self._NO_COLORS = True
        for k in colors.keys():
            colors[k] = ''

    def newline(self):
        '''Print a newline character (\n) on Standard Output.'''

        sys.stdout.write('\n')

    def raise_last(self, exc):
        raise exc(self.last_msg)

    @ property
    def last_msg(self):
        return self._stack[-1]

    def verbose(self, msg, *a, **kw):
        self.log(self.VERBOSE, 'std', msg, *a, **kw)

    def debug(self, msg, *a, **kw):
        self.log(self.DEBUG, 'std', msg, *a, **kw)

    def info(self, msg, *a, **kw):
        self.log(self.INFO, 'std', msg, *a, **kw)

    def success(self, msg, *a, **kw):
        self.log(self.INFO, 'good', msg, *a, **kw)

    def warn(self, msg, *a, **kw):
        self.log(self.WARN, 'warn', msg, *a, **kw)

    def error(self, msg, *a, **kw):
        self.log(self.ERROR, 'bad', msg, *a, **kw)
        exc = kw.get('exc', None)
        if exc is not None:
            raise exc(self.last_msg)

    def fatal(self, msg, *a, **kw):
        self.log(self.FATAL, 'vbad', msg, *a, **kw)
        exc = kw.get('exc', None)
        if exc is not None:
            raise exc(self.last_msg)

    def exit(self, msg=None, status=1):
        if msg != None:
            self.log(self.FATAL, 'vbad', msg)
        sys.exit(status)

    def log(self, level, col, msg, *a, **kw):
        '''
        This is the base function that logs all messages. This function prints a newline character too,
        unless you specify ``addn=False``. When the message starts with a return character (\r) it automatically
        cleans the line.
        '''

        if level >= self.level and self.enabled:
            std = sys.stdout
            if level >= self.ERROR:
                std = sys.stderr

            ## We can pass to logger.log any object: it must have at least
            ## a __repr__ or a __str__ method.
            msg = str(msg)
            if msg.startswith('\r'):
                ## We have to clear the line in case this message is longer than
                ## the previous

                std.write('\r' + ' ' * len(self.last_msg))
                msg = '\r' + ' ' * self.indent + msg[1:].format(*a)
            else:
                try:
                    msg = ' ' * self.indent + msg.format(*a)
                except KeyError:
                    msg = ' ' * self.indent + msg

            col, col_reset = colors[col], colors['reset']
            if self._NO_COLORS:
                col, col_reset = '', ''
            std.write(col + msg + col_reset)

            ## Automatically adds a newline character
            if kw.get('addn', True):
                self.newline()

            ## flush() makes the log immediately readable
            std.flush()
            self._stack.append(msg)


logger = Logger()
