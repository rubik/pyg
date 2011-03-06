import sys
import logging


class Logger(object):

    VERBOSE = logging.DEBUG - 1
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    NOTIFY = (logging.INFO + logging.WARNING) / 2
    WARN = logging.WARNING
    ERROR = logging.ERROR
    FATAL = logging.FATAL

    def __init__(self):
        self.indent = 0
        self.level = Logger.DEBUG

    def verbose(self, msg):
        return self.log(self.VERBOSE, msg)

    def debug(self, msg):
        return self.log(self.DEBUG, msg)

    def info(self, msg):
        return self.log(self.INFO, msg)

    def notify(self, msg):
        return self.log(self.NOTIFY, msg)

    def warn(self, msg):
        return self.log(self.WARN, msg)

    def error(self, msg):
        return self.log(self.ERROR, msg)

    def fatal(self, msg):
        return self.log(self.FATAL, msg)

    def log(self, level, msg):
        if level >= self.level:
            sys.stdout.write(' ' * self.indent + msg)
            sys.stdout.write('\n')
            sys.stdout.flush()
            #logging.log(level, msg)


logger = Logger()