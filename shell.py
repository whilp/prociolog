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
