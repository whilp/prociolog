import pexpect
import subprocess

from subprocess import PIPE

SHELL = ["/bin/sh"]
SSH = ["/usr/bin/ssh"]

def LoggingDescriptor(fd):
    return fd

class Shell(subprocess.Popen):
    defaults = {
        "stdin": PIPE,
        "stdout": PIPE,
        "stderr": PIPE,
    }

    def __init__(self, args=SHELL, **kwargs):
        defaults = self.defaults.copy()
        defaults.update(kwargs)
        subprocess.Popen.__init__(self, args, **defaults)
        self.stdin = LoggingDescriptor(self.stdin)
        self.stdout = LoggingDescriptor(self.stdout)
        self.stderr = LoggingDescriptor(self.stderr)

class RemoteShell(Shell):

    def __init__(self, args=None, hostname="localhost", **kwargs):
        if args is None:
            args = SHELL
        args = SSH + [hostname] + args
        Shell.__init__(self, args=args, **kwargs)
