#coding: utf-8
from __future__ import unicode_literals, absolute_import

from importlib import import_module
import os
import re

from .exceptions import InvalidFile, UnknownCamera

seq_re = re.compile(r'(\d{4,})')


class Photo(object):

    def __init__(self, filename, exiftool_instance):
        self._filename = filename

        self._metadata = exiftool_instance.get_metadata(self._filename)

        try:
            maker = self['EXIF:Make']
            model = self['EXIF:Model']
        except IndexError:
            raise InvalidFile('Can`t read camera info')

        module_path = ['d3_convert.camera', maker.lower().replace(' ', '_'), model.lower().replace(' ', '_')]
        module_name = '.'.join(module_path)

        try:
            module = import_module(module_name)
        except ImportError:
            raise UnknownCamera('Unknown Camera: {0} {1}'.format(maker, model))

        camera_model = getattr(module, 'Camera')

        self.camera = camera_model(self)

    @property
    def filename(self):
        return self._filename

    @property
    def dirname(self):
        return os.path.abspath(os.path.dirname(self.filename))

    @property
    def seq_number(self):
        return int(seq_re.findall(self.filename)[0])

    def __getitem__(self, item):
        if isinstance(item, slice):
            raise TypeError('Slicing not allowed')

        if item in self._metadata:
            return self._metadata[item]
        else:
            raise IndexError('EXIF Tag {0} not found'.format(item))

    def __getattr__(self, item):
        if hasattr(self.camera, item):
            return getattr(self.camera, item)
        raise AttributeError('`{0}` object has no attribute `{1}`'.format(self.__class__.__name__, item))

    def __str__(self):
        return self.filename

    __unicode__ = __str__

    def __repr__(self):
        return '<Photo: {0}>'.format(self.filename)
