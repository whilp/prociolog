import logging

from subprocess import PIPE, Popen

try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record): pass

__all__ = ["IOLogger", "LineLogger", "LoggingCmd", "wrapfd"]

LOGGER = "cmdlog"

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
    level = logging.DEBUG
    """Default level used by :meth:`log`."""

    def __init__(self, fd, logger):
        self.fd = fd
        self.logger = logger

    def log(self, str, *args, **kwargs):
        """Log intercepted data.

        Arguments are as for :method:`logging.Logger.log`, except *level* is
        pulled from *kwargs* if present; otherwise, :attr:`level` is used.
        """
        _kwargs = kwargs.copy()
        level = _kwargs.pop("level", self.level)
        self.logger.log(level, repr(str), *args, **kwargs)

def wrapfd(fd, logger, wrapper):
    """Wrap a file object with a logging wrapper.

    *fd* should be a file object; *logger* should be a :class:`logging.Logger`
    instance. *wrapper* should take *fd* and *logger* as its two arguments and
    supply *readers* and *writers* attributes; typically, it will be the
    :class:`IOLogger` class or a subclass. This function instantiates the wrapper
    and assigns the attributes of *fd* to it, skipping over methods identified
    in the *readers* and *writers* attributes.

    Returns a wrapped file object.
    """
    wrapped = wrapper(fd, logger)
    attrs = (a for a in dir(wrapped.fd) 
            if a not in (wrapper.readers + wrapper.writers))
    for attr in attrs:
        try:
            setattr(wrapped, attr, getattr(fd, attr))
        except TypeError:
            pass

    return wrapped

def reader(reader):
    """Wrap a reader method of a wrapped file object.

    *reader* is the name of the method. The wrapped method will call the wrapped
    file object's *log* method (typically :meth:`IOLogger.log`) after calling
    the *reader* method.
    """
    def wrapper(self, size=-1, *args, **kwargs):
        method = getattr(self.fd, reader)
        str = method(size)
        self.log(str, *args, **kwargs)
        return str
    return wrapper

def writer(writer):
    """Wrap a writer method of a wrapped file object.

    *writer* is the name of the method. The wrapped method will call the wrapped
    file object's *log* method (typically :meth:`IOLogger.log`) before calling
    the *writer* method.
    """
    def wrapper(self, str, *args, **kwargs):
        method = getattr(self.fd, writer)
        self.log(str, *args, **kwargs)
        return method(str)
    return wrapper

# Fill in the IOLogger's reader and writer methods.
for name in IOLogger.readers:
    setattr(IOLogger, name, reader(name))
for name in IOLogger.writers:
    setattr(IOLogger, name, writer(name))

class LineLogger(IOLogger):
    """Log each line of IO as it's written to or read from the wrapped file object.
    """
    newline = "\n"
    """The newline character(s)."""

    def __init__(self, fd, logger):
        IOLogger.__init__(self, fd, logger)
        self.readbuf = []
        self.writebuf = []

    def read(self, size=-1, *args, **kwargs):
        data = self.fd.read(size)
        chunks = data.splitlines(True)
        if not chunks:
            return data
        elif self.readbuf:
            chunks[0] = ''.join(self.readbuf + [chunks[0]])
            self.readbuf = []

        for chunk in chunks:
            if not chunk.endswith(self.newline):
                self.readbuf.append(chunk)
                break
            self.log(chunk, *args, **kwargs)
        return data

    def write(self, str, *args, **kwargs):
        self.fd.write(str)
        chunks = str.splitlines(True)
        if not chunks:
            return
        elif self.writebuf:
            chunks[0] = ''.join(self.writebuf + [chunks[0]])
            self.writebuf = []

        for chunk in chunks:
            if not chunk.endswith(self.newline):
                self.writebuf.append(chunk)
                break
            self.log(chunk, *args, **kwargs)

    def writelines(self, strings, *args, **kwargs):
        for str in strings:
            self.write(str, *args, **kwargs)
    
class LoggingCmd(Popen):
    """A command subprocess that logs its IO.

    Any data written to or read from the process' file objects will be sent
    to a child of the process' main logger.

    Parameters are:

        * *args* command arguments (like :class:`subprocess.Popen`);
        * *logger* a :class:`logging.Logger` instance (or something that has a
          *name* attribute); and
        * *kwargs*, which are passed on to :class:`subprocess.Popen`.
    """
    fdnames = ("stdin", "stderr", "stdout")
    """File objects that should be wrapped."""
    wrapper = IOLogger
    """Wrapper class for the process' file objects."""

    def __init__(self, args, logger, **kwargs):
        _kwargs = kwargs.copy()
        for fdname in self.fdnames:
            _kwargs[fdname] = PIPE
        Popen.__init__(self, args, **_kwargs)
        self.logger = logger
        self.wrapfds()

    def wrapfds(self):
        """Wrap the process' file objects.

        Creates a logger for each file object (see :attr:`fdnames` and
        :attr:`wrapper`).
        """
        name = self.logger.name
        for fdname in self.fdnames:
            fd = getattr(self, fdname)
            logger = logging.getLogger(name + '.' + fdname)
            setattr(self, fdname, wrapfd(fd, logger, self.wrapper))
