#coding: utf-8
from __future__ import unicode_literals, absolute_import


class CameraBase(object):

    def __init__(self, photo):
        self.photo = photo

    @property
    def is_bracketed(self):
        raise NotImplementedError()

    @property
    def bracket_value(self):
        raise NotImplementedError()

    @property
    def bracket_count(self):
        #TODO: определять количество кадров
        return 3
