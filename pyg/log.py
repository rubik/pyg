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
        self.level = Logger.INFO

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

    def fatal(self, msg, *a, **kw):
        self.log(self.FATAL, msg, *a, **kw)

    def log(self, level, msg, *a, **kw):
        if level >= self.level:
            msg = ' ' * self.indent + msg.format(*a)
            sys.stdout.write(msg)

            ## Automatically adds a newline character
            sys.stdout.write('\n')

            ## flush() makes the log immediately readable
            sys.stdout.flush()


logger = Logger()
