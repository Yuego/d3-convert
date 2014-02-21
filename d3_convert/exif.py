#coding: utf-8
from __future__ import unicode_literals, absolute_import


try:
    from gi.repository import GExiv2 as exif
except ImportError:
    class exif(object):
        def __init__(self, path):
            self.path = path

        def __getitem__(self, item):
            raise NotImplementedError()
