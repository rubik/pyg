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
        import os, pwd
        try:
            home = pwd.getpwnam(os.getlogin()).pw_dir
        except OSError:
            home = pwd.getpwuid(os.getuid()).pw_dir
        os.makedirs(home)
        self._logger = logging.basicConfig(filename=os.path.join(home,
                                                                 '.pyg', 'pyg.log'),
                                           level=logging.DEBUG)
        self.indent = 0
        self.level = Logger.DEBUG

    def verbose(self, msg, **kw):
        return self.log(self.VERBOSE, msg, **kw)

    def debug(self, msg, **kw):
        return self.log(self.DEBUG, msg, **kw)

    def info(self, msg, **kw):
        return self.log(self.INFO, msg, **kw)

    def notify(self, msg, **kw):
        return self.log(self.NOTIFY, msg, **kw)

    def warn(self, msg, **kw):
        return self.log(self.WARN, msg, **kw)

    def error(self, msg, **kw):
        return self.log(self.ERROR, msg, **kw)

    def fatal(self, msg, **kw):
        return self.log(self.FATAL, msg, **kw)

    def log(self, level, msg, **kw):
        if level >= self.level:
            msg = ' ' * self.indent + msg
            sys.stdout.write(msg)
            if kw.get('addn', True):
                sys.stdout.write('\n')
            sys.stdout.flush()
            logging.log(level, msg)


logger = Logger()