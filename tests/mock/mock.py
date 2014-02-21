#coding: utf-8
from __future__ import unicode_literals, absolute_import


class exif(object):

    _data = {
        'Exif.Image.Make': 'Canon',
        'Exif.Image.Model': 'Canon EOS 7D',
    }

    def __init__(self, path):
        self.path = path

    def __getitem__(self, item):
        return self._data.get(item, None)
