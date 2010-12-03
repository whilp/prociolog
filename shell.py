import logging

from subprocess import PIPE, Popen

try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record): pass

log = logging.getLogger("shell")
log.addHandler(NullHandler())

SHELL = ["/bin/sh"]
SSH = ["/usr/bin/ssh"]

def LoggingDescriptor(fd):
    return fd

class IOLogger(object):
    protect = ("log", "read", "readline", "write")
    logname = "shell.io"

    def __init__(self, fd, name):
        self.fd = fd
        self.logname = IOLogger.logname + '.' + name

    def log(self, str, *args, **kwargs):
        logger = logging.getLogger(self.logname)
        _kwargs = kwargs.copy()
        level = _kwargs.pop("level", logging.DEBUG)
        logger.log(level, repr(str), *args, **kwargs)

    def read(self, size=None, *args, **kwargs):
        str = self.fd.read(size)
        self.log(str, *args, **kwargs)
        return str

    def readline(self, size=-1, *args, **kwargs):
        str = self.fd.readline(size)
        self.log(str, *args, **kwargs)
        return str

    def readlines(self, size=-1, *args, **kwargs):
        str = self.fd.readlines(size)
        self.log(str, *args, **kwargs)
        return str

    def write(self, str, *args, **kwargs):
        self.log(str, *args, **kwargs)
        return self.fd.write(str)

    @staticmethod
    def wrapfd(fd, name):
        wrapped = IOLogger(fd, name)
        attrs = (a for a in dir(fd) if a not in IOLogger.protect)
        for attr in attrs:
            try:
                setattr(wrapped, attr, getattr(fd, attr))
            except TypeError:
                pass

        return wrapped

class Shell(Popen):
    defaults = {
        "stdin": PIPE,
        "stdout": PIPE,
        "stderr": PIPE,
    }

    def __init__(self, args=SHELL, **kwargs):
        defaults = self.defaults.copy()
        defaults.update(kwargs)
        Popen.__init__(self, args, **defaults)
        self.stdin = LoggingDescriptor(self.stdin)
        self.stdout = LoggingDescriptor(self.stdout)
        self.stderr = LoggingDescriptor(self.stderr)

class RemoteShell(Shell):

    def __init__(self, args=None, hostname="localhost", **kwargs):
        if args is None:
            args = SHELL
        args = SSH + [hostname] + args
        Shell.__init__(self, args=args, **kwargs)
