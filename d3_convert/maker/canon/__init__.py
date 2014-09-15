#coding: utf-8

from d3_convert.maker.base import MakerBase


class Maker(MakerBase):

    def is_bracketed(self):
        mode = int(self.exif['Exif.CanonFi.BracketMode'])
        return mode == 1

    def bracket_value(self):
        value = int(self.exif['Exif.CanonFi.BracketValue'])
        return value

