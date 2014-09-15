#coding: utf-8

from d3_convert.exif import exif
from importlib import import_module
import os
import re

seq_re = re.compile(r'(\d{4,})')


class Photo(object):
    exif_class = exif
    maker_module = 'd3_convert.maker'

    def __init__(self, raw=None, tif=None):
        self._raw_file = raw
        self._tif_file = tif

        self._filename = None

        self._exif = None
        self._data = None

    def _get_raw(self):
        return self._raw_file
    raw = property(_get_raw)

    def _get_raw_dir(self):
        if self._raw_file is None:
            return None
        return os.path.abspath(os.path.dirname(self._raw_file))
    raw_dir = property(_get_raw_dir)

    def _get_filename(self):
        if self._filename is None:
            if self._raw_file is not None:
                filename = os.path.basename(self._raw_file)
            elif self._tif_file is not None:
                filename = os.path.basename(self._tif_file)
            else:
                raise ValueError('Where is file???')

            name, _n, ext = filename.rpartition('.')
            if not name:
                name = ext
            self._filename = name
        return self._filename
    filename = property(_get_filename)

    def _get_sequence_number(self):
        return int(seq_re.findall(self.filename)[0])
    seq_number = property(_get_sequence_number)

    def _get_tif(self):
        return self._tif_file
    tif = property(fget=_get_tif)

    def _get_tif_dir(self):
        if self._tif_file is None:
            return None
        return os.path.abspath(os.path.dirname(self._tif_file))

    def _set_tif_dir(self, path):
        if self._tif_file is not None:
            raise ValueError('Tif moved?')
        self._tif_file = os.path.join(path, '{0}.tif'.format(self.filename))
    tif_dir = property(fget=_get_tif_dir, fset=_set_tif_dir)

    def _get_exif(self):
        if self._exif is None:
            if self.raw:
                self._exif = self.exif_class(self.raw)
            else:
                self._exif = self.exif_class(self.tif)
        return self._exif
    exif = property(_get_exif)

    def _get_data(self):
        if self._data is None:
            make = self.exif['Exif.Image.Make'].lower()
            model = self.exif['Exif.Image.Model'].lower()

            module_path = [self.maker_module, make, model]
            module_name = '.'.join(module_path)

            try:
                module = import_module(module_name)
            except ImportError:  # импортируем общий для всех камер модуль
                module_path.pop()
                module_name = '.'.join(module_path)
                module = import_module(module_name)

            maker = getattr(module, 'Maker')

            self._data = maker(self, self.exif)

        return self._data
    data = property(_get_data)

    @property
    def is_bracketed(self):
        return self.data.is_bracketed()

    @property
    def bracket_value(self):
        return self.data.bracket_value()

    @property
    def bracket_count(self):
        return self.data.bracket_count()

    @property
    def exposure(self):
        return self.data.exposure()

    def __unicode__(self):
        if self.raw:
            return self.raw
        else:
            return self.tif
    __str__ = __unicode__

    def __repr__(self):
        return '<Photo `{0}`>'.format(self.__unicode__())
