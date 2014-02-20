#coding: utf-8
from __future__ import unicode_literals, absolute_import

from .photo import Photo


class TifPhoto(Photo):

    def _get_exif(self):
        if self._exif is None:
            raise NotImplemented()
        return self._exif
