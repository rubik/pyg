import sys
import logging


__all__ = ['logger']


class Logger(object):

    VERBOSE = logging.DEBUG - 1
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    def __init__(self,level=None):
        self.indent = 0
        self.level = level or Logger.INFO
        self.last_msg = ''
        self.enabled = True

    def newline(self):
        '''
        Print a newline character (\n) on Standard Output.
        '''

        sys.stdout.write('\n')

    def verbose(self, msg, *a, **kw):
        self.log(self.VERBOSE, msg, *a, **kw)

    def debug(self, msg, *a, **kw):
        self.log(self.DEBUG, msg, *a, **kw)

    def info(self, msg, *a, **kw):
        self.log(self.INFO, msg, *a, **kw)

    def warn(self, msg, *a, **kw):
        self.log(self.WARN, msg, *a, **kw)

    def error(self, msg, *a, **kw):
        self.log(self.ERROR, msg, *a, **kw)
        exc = kw.get('exc', None)
        if exc is not None:
            raise exc(self.last_msg)

    def fatal(self, msg, *a, **kw):
        self.log(self.FATAL, msg, *a, **kw)
        exc = kw.get('exc', None)
        if exc is not None:
            raise exc(self.last_msg)

    def log(self, level, msg, *a, **kw):
        '''
        This is the base function that logs all messages. This function prints a newline character too,
        unless you specify ``addn=False``. When the message starts with a return character (\r) it automatically
        cleans the line.
        '''

        if level >= self.level and self.enabled:
            std = sys.stdout
            if level >= self.ERROR:
                std = sys.stderr
            if msg.startswith('\r'):
                ## We have to clear the line in case this message is longer than
                ## the previous

                std.write('\r' + ' ' * len(self.last_msg))
                msg = '\r' + ' ' * self.indent + msg[1:].format(*a)
            else:
                msg = ' ' * self.indent + msg.format(*a)
            std.write(msg)

            ## Automatically adds a newline character
            if kw.get('addn', True):
                std.write('\n')

            ## flush() makes the log immediately readable
            std.flush()
            self.last_msg = msg


logger = Logger()
