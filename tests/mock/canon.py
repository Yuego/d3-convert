#coding: utf-8
from __future__ import unicode_literals, absolute_import


class Maker(object):

    def __init__(self, *args, **kwargs):
        pass

    def is_bracketed(self):
        return True

    def bracket_value(self):
        return 0

    def bracket_count(self):
        return 3
