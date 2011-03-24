import sys
import logging


class Logger(object):

    VERBOSE = logging.DEBUG - 1
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    def __init__(self):
        self.indent = 0
        self.level = Logger.DEBUG

    def verbose(self, msg, **kw):
        self.log(self.VERBOSE, msg, **kw)

    def debug(self, msg, **kw):
        self.log(self.DEBUG, msg, **kw)

    def info(self, msg, **kw):
        self.log(self.INFO, msg, **kw)

    def warn(self, msg, **kw):
        self.log(self.WARN, msg, **kw)

    ## For error and fatal we can raise exceptions after the log
    def error(self, msg, exc=None, **kw):
        self.log(self.ERROR, msg, **kw)
        if exc is not None:
            raise exc(msg)

    def fatal(self, msg, exc=None, **kw):
        self.log(self.FATAL, msg, **kw)
        if exc is not None:
            raise exc(msg)

    def log(self, level, msg, **kw):
        if level >= self.level:
            msg = ' ' * self.indent + msg
            sys.stdout.write(msg)
            ## Use the `addn` keyword arg to add a newline character
            if kw.get('addn', True):
                sys.stdout.write('\n')

            ## flush() makes the log immediately readable
            sys.stdout.flush()


logger = Logger()
