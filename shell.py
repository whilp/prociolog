import logging

from subprocess import PIPE, Popen

try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record): pass

LOGGER = "shell"
IOLOGGER = LOGGER + ".io"
SHELL = ["/bin/sh"]
SSH = ["/usr/bin/ssh"]

log = logging.getLogger(LOGGER)
log.addHandler(NullHandler())

class IOLogger(object):
    """Intercept and log IO operations.

    The *IOLogger* wraps a file object's read and write methods and passes the
    incoming or outgoing data to a logger.

    Parameters are:

        * *fd* a file object; and
        * *logger* the logger to which intercepted data will be passed.
    """
    readers = ("read", "readline", "readlines")
    """Read methods on the file object that should be wrapped."""
    writers = ("write", "writelines")
    """Write methods on the file object that should be wrapped."""

    def __init__(self, fd, logger):
        self.fd = fd
        self.logger = logger

    def log(self, str, *args, **kwargs):
        _kwargs = kwargs.copy()
        level = _kwargs.pop("level", logging.DEBUG)
        self.logger.log(level, repr(str), *args, **kwargs)

def wrapfd(fd, logger):
    wrapped = IOLogger(fd, logger)
    attrs = (a for a in dir(fd) if a not in (IOLogger.readers + IOLogger.writers))
    for attr in attrs:
        try:
            setattr(wrapped, attr, getattr(fd, attr))
        except TypeError:
            pass

    return wrapped

def reader(reader):
    def wrapper(self, size=-1, *args, **kwargs):
        method = getattr(self.fd, reader)
        str = method(size)
        self.log(str, *args, **kwargs)
        return str
    return wrapper

def writer(writer):
    def wrapper(self, str, *args, **kwargs):
        method = getattr(self.fd, writer)
        self.log(str, *args, **kwargs)
        return method(str)
    return wrapper

for name in IOLogger.readers:
    setattr(IOLogger, name, reader(name))
for name in IOLogger.writers:
    setattr(IOLogger, name, writer(name))
    
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
            logger = logging.getLogger(IOLOGGER + '.' + self.hostname + '.' + fdname)
            setattr(self, fdname, wrapfd(fd, logger))

class RemoteShell(Shell):

    def __init__(self, args=None, hostname="localhost", **kwargs):
        self.hostname = hostname

        if args is None:
            args = SHELL
        args = SSH + [hostname] + args
        Shell.__init__(self, args=args, **kwargs)
