#coding: utf-8
from __future__ import unicode_literals, absolute_import


class Log(object):

    def __init__(self):
        self.enabled = True

    def trace(self, *args):
        if self.enabled:
            print(' '.join(args))

log = Log()
