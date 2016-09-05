#coding: utf-8
from __future__ import unicode_literals, absolute_import

from importlib import import_module
import os
import re

from .processing.commands import copy_exif_to_cmd
from .exceptions import InvalidFile, UnknownCamera
from .utils.process import Process

seq_re = re.compile(r'(\d{4,})')


class Photo(object):

    def __init__(self, filename, metadata=None, exclude_tags=None):
        self._filename = filename
        self._name = None
        self._type = None

        if isinstance(metadata, Photo):
            self.update_metadata(src_photo=metadata, excludes=exclude_tags)
            metadata = metadata.get_metadata()

        self._metadata = self.filter_metadata(metadata=metadata, excludes=exclude_tags)

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

    def filter_metadata(self, metadata, excludes=None):
        if excludes and isinstance(excludes, (list, tuple)):
            for tag in excludes:
                metadata.pop(tag, None)
        return metadata

    @property
    def filename(self):
        return self._filename

    @property
    def basename(self):
        return os.path.basename(self.filename)

    @property
    def name(self):
        if self._name is None:
            name, _, ext = self.basename.rpartition('.')
            if not name:
                name = ext
            self._name = name
        return self._name

    @property
    def type(self):
        if self._type is None:
            name, _, ext = self.basename.rpartition('.')
            self._type = ext.lower()
        return self._type

    @property
    def dirname(self):
        return os.path.abspath(os.path.dirname(self.filename))

    def get_metadata(self):
        return self._metadata.copy()

    def update_metadata(self, src_photo, excludes=None):
        cmd = copy_exif_to_cmd(src_photo=src_photo, dst_photo=self, excludes=excludes)

        p = Process(cmd, cwd=self.dirname)
        p.run()

        result = ' '.join([p.result, p.errors]).lower()
        if 'updated' not in result:
            raise RuntimeError('Can`t update EXIF info for: {0}'.format(self.filename))

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

    def __eq__(self, other):
        return self.seq_number == other.seq_number

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.seq_number

    def __str__(self):
        return self.filename

    __unicode__ = __str__

    def __repr__(self):
        return '<Photo: {0}>'.format(self.filename)


class TiffPhoto(Photo):

    def __repr__(self):
        return '<TiffPhoto: {0}>'.format(self.filename)


class BlendPhoto(Photo):

    def __repr__(self):
        return '<BlendPhoto: {0}>'.format(self.filename)
