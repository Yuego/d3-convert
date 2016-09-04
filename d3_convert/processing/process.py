#coding: utf-8
from __future__ import unicode_literals, absolute_import

import subprocess as sp


class Process(object):

    def __init__(self, command, *args, **kwargs):
        self.cmd = command

        self.stdin = kwargs.get('stdin', sp.PIPE)
        self.stdout = kwargs.get('stdout', sp.PIPE)
        self.stderr = kwargs.get('stderr', sp.PIPE)

        self.envdict = kwargs.get('envdict', {})
        self.cwd = kwargs.get('cwd', None)

        self.pipe = None
        self.out = None
        self.err = None

        self.iterator = None

    def _open(self):
        if self.pipe is None:
            self.pipe = sp.Popen(
                self.cmd,
                stdin=self.stdin,
                stdout=self.stdout,
                stderr=self.stderr,
                cwd=self.cwd,
                env=self.envdict,
            )

    def _close(self):
        self.pipe = None
        self.out = None
        self.err = None

    def close(self):
        if self.pipe is not None:
            self.pipe.stdin.close()
            self._close()

    def run(self):
        self._read()

    def wait(self):
        self.pipe.wait()

    def kill(self):
        if self.pipe is not None:
            self.pipe.kill()
            self._close()

    def write(self, data):
        self._open()
        self.pipe.stdin.write(data)
        self.pipe.stdin.flush()

    def _read(self):
        self._open()
        if self.out is None:
            out, err = self.pipe.communicate()
            self.out, self.err = out.decode('utf-8'), err.decode('utf-8')

    def readlines(self):
        self._read()
        return self.out.split('\n')

    def __iter__(self):
        if self.iterator is None:
            self.iterator = iter(self.readlines())
        return self.iterator

    def next(self):
        return self.__iter__().next()

    def _read_out(self):
        self._read()
        return self.out

    result = property(_read_out)

    def _read_errors(self):
        self._read()
        return self.err

    errors = property(_read_errors)

    def _code(self):
        self._read()
        return self.pipe.returncode

    code = property(_code)

    def _success(self):
        return self.code == 0

    def _failed(self):
        return not self._success()

    success = property(_success)
    failed = property(_failed)


