#coding: utf-8
from __future__ import unicode_literals, absolute_import

from nose.tools import assert_raises

from d3_convert.maker.base import MakerBase


class TestMakerBase(object):

    def setUp(self):
        self.mb = MakerBase(photo=None, exif=None)

    def teardown(self):
        pass

    def test_is_bracketed_raises_not_implemented(self):
        assert_raises(NotImplementedError, self.mb.is_bracketed)

    def test_bracket_value_raises_not_implemented(self):
        assert_raises(NotImplementedError, self.mb.bracket_value)

    def test_bracket_count_returns_3(self):
        assert self.mb.bracket_count() == 3
