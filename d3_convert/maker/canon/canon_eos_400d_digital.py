#coding: utf-8
from __future__ import unicode_literals, absolute_import


from d3_convert.maker.canon import Maker as MakerBase

#TODO: проверить на реальных фото
class Maker(MakerBase):

    def is_bracketed(self):
        mode = self.exif['Exif.Photo.ExposureMode']
        return mode == 1
