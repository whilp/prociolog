import subprocess

from subprocess import PIPE

class Shell(subprocess.Popen):
    cmd = "/bin/sh"
    defaults = {
        "stdin": PIPE,
        "stdout": PIPE,
        "stderr": PIPE,
    }

    def __init__(self, args=None, **kwargs):
        if args is None:
            args = [self.cmd]
        defaults = self.defaults.copy()
        defaults.update(kwargs)
        subprocess.Popen.__init__(self, args, **defaults)
