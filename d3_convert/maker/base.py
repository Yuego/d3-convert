#coding: utf-8
from __future__ import unicode_literals, absolute_import


class MakerBase(object):

    def __init__(self, exif):
        self.exif = exif

    def is_bracketed(self):
        raise NotImplemented()

    def bracket_value(self):
        raise NotImplemented()

    def bracket_count(self):
        #TODO: определять количество кадров
        return 3
