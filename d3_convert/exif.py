#coding: utf-8


try:
    from gi.repository import GExiv2
    exif = GExiv2.Metadata
except ImportError:
    class exif(object):
        def __init__(self, path):
            self.path = path

        def __getitem__(self, item):
            raise NotImplementedError()
