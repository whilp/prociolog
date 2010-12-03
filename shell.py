import logging

from subprocess import PIPE, Popen

try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record): pass

LOGGER = "shell"
SHELL = ["/bin/sh"]
SSH = ["/usr/bin/ssh"]

log = logging.getLogger(LOGGER)
log.addHandler(NullHandler())

class IOLogger(object):
    protect = ("log", "read", "readline", "write")
    logname = LOGGER + ".io"

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
    fdnames = ("stdin", "stderr", "stdout")

    def __init__(self, args=SHELL, **kwargs):
        _kwargs = kwargs.copy()
        for fdname in self.fdnames:
            _kwargs[fdname] = PIPE
        Popen.__init__(self, args, **_kwargs)
        self.hostname = "localhost"
        self.wrapfds()

    def wrapfds(self):
        for fdname in self.fdnames:
            fd = getattr(self, fdname)
            name = self.hostname + '.' + fdname
            setattr(self, fdname, IOLogger.wrapfd(fd, name))

class RemoteShell(Shell):

    def __init__(self, args=None, hostname="localhost", **kwargs):
        self.hostname = hostname

        if args is None:
            args = SHELL
        args = SSH + [hostname] + args
        Shell.__init__(self, args=args, **kwargs)
