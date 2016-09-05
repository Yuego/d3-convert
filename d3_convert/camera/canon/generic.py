#coding: utf-8
from __future__ import unicode_literals, absolute_import

from d3_convert.camera.base import CameraBase


class GenericCamera(CameraBase):

    @property
    def is_bracketed(self):
        mode = int(self.photo['MakerNotes:BracketMode'])
        return mode == 1

    @property
    def bracket_value(self):
        return int(self.photo['MakerNotes:BracketValue'])

    @property
    def bracket_count(self):
        bc = self.photo['MakerNotes:AEBShotCount']
        return int(bc.split(' ')[0])


class Camera(GenericCamera):
    pass
