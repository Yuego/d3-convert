#coding: utf-8
from __future__ import unicode_literals, absolute_import

from .generic import GenericCamera


#TODO: проверить на реальных фото
class Camera(GenericCamera):

    @property
    def is_bracketed(self):
        mode = self.photo['Exif.Photo.ExposureMode']
        return mode == 1
