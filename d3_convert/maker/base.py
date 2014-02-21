#coding: utf-8
from __future__ import unicode_literals, absolute_import


class MakerBase(object):

    def __init__(self, photo, exif):
        self.photo = photo
        self.exif = exif

    def is_bracketed(self):
        raise NotImplementedError()

    def bracket_value(self):
        raise NotImplementedError()

    def bracket_count(self):
        #TODO: определять количество кадров
        return 3
