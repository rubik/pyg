import os
import sys
import logging


__all__ = ['logger']

try:
    from colorama import init, Fore, Style
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


def get_console_width():
    """
    Return width of available window area. Autodetection works for
    Windows and POSIX platforms. Returns 80 for others

       Code from http://bitbucket.org/techtonik/python-wget
    """

    if os.name == 'nt':
        STD_INPUT_HANDLE  = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE  = -12

        # get console handle
        from ctypes import windll, Structure, byref
        try:
            from ctypes.wintypes import SHORT, WORD, DWORD
        except ImportError:
            # workaround for missing types in Python 2.5
            from ctypes import (
                c_short as SHORT, c_ushort as WORD, c_ulong as DWORD)
        console_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        # CONSOLE_SCREEN_BUFFER_INFO Structure
        class COORD(Structure):
            _fields_ = [("X", SHORT), ("Y", SHORT)]

        class SMALL_RECT(Structure):
            _fields_ = [("Left", SHORT), ("Top", SHORT),
                        ("Right", SHORT), ("Bottom", SHORT)]

        class CONSOLE_SCREEN_BUFFER_INFO(Structure):
            _fields_ = [("dwSize", COORD),
                        ("dwCursorPosition", COORD),
                        ("wAttributes", WORD),
                        ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", DWORD)]

        sbi = CONSOLE_SCREEN_BUFFER_INFO()
        ret = windll.kernel32.GetConsoleScreenBufferInfo(console_handle, byref(sbi))
        if ret == 0:
            return 0
        return sbi.srWindow.Right+1

    elif os.name == 'posix':
        from fcntl import ioctl
        from termios import TIOCGWINSZ
        from array import array

        winsize = array("H", [0] * 4)
        try:
            ioctl(sys.stdout.fileno(), TIOCGWINSZ, winsize)
        except IOError:
            pass
        return (winsize[1], winsize[0])[0]

    return 80


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
        self._stack = ['']
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

    @property
    def last_msg(self):
        return self._stack[-1]

    def ask(self, message=None, bool=None, choices=None, dont_ask=False):
        if bool is not None:
            if bool in (True, False) or (isinstance(bool, (list, tuple)) and len(bool) == 1):
                if bool == False:
                    txt = "Cancel"
                elif bool == True:
                    txt = "OK"
                else:
                    txt = bool[0]
                self.log(self.info, 'std', "%s, %s..."%(message, txt), addn=False)
                if not dont_ask:
                    raw_input()
                return
            else:
                if dont_ask:
                    self.log(self.info, 'std', '%s ? Yes'%message)
                    return True

                while True:
                    self.log(self.info, 'std', "yes: "+bool[0])
                    self.log(self.info, 'std', "no: "+bool[1])
                    try:
                        self.log(self.info, 'std', '%s ? (y/[n]) '%message, addn=False)
                        ans = raw_input()
                    except Exception:
                        continue

                    # default choice : no
                    if not ans.strip():
                        return False

                    if ans not in 'yYnN':
                        continue

                    return ans in 'yY'

        if choices:
            if isinstance(choices, dict):
                _data = choices
                choices = choices.keys()
            else:
                _data = None

            self.log(self.info, 'std', message)
            for n, choice in enumerate(choices):
                self.log(self.info, 'std', "%2d - %s"%(n+1, choice))

            while True:
                try:
                    ans = input('Your choice ? ')
                except Exception:
                    self.log(self.info, 'std', "Please enter selected option's number.")
                    continue
                if ans < 0 or ans > len(choices):
                    continue
                break

            idx = choices[ans-1]
            return (_data[idx] if _data else idx)

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
            if msg.startswith('\r') or self.last_msg.startswith('\r'):
                ## We have to clear the line in case this message is longer than
                ## the previous

                std.write('\r' + ' ' * get_console_width())
                msg = '\r' + ' ' * self.indent + msg.lstrip('\r').format(*a)
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
if __name__ == '__main__':
    print logger.ask("Beware, you enter a secret place", bool=True)
    print logger.ask("Sorry, can't install this package", bool=False)
    print logger.ask("Sorry, can't install this package", bool=['Press any key to continue'])
    print logger.ask('Proceed', bool=('remove files', 'cancel'))
    print logger.ask('Do you want to upgrade', bool=('upgrade version', 'keep working version'))
    print logger.ask('Installation method', choices=('Egg based', 'Flat directory'))
    print logger.ask('some dict', choices={'choice a': 'a', 'choice b': 'b', 'choice c': 'c'})
