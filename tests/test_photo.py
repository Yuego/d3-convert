#coding: utf-8
from __future__ import unicode_literals, absolute_import

from nose.tools import assert_raises, assert_is_instance
from d3_convert.photo.photo import Photo
from .mock import exif
from .mock.canon import Maker


class MockPhoto(Photo):
    exif_class = exif
    maker_module = 'tests.mock'


class TestRawPhoto(object):

    def setUp(self):
        self.p = MockPhoto(raw='/path/file_1234.raw')

    def test_raw_property_ro(self):
        assert self.p.raw == '/path/file_1234.raw'

        def _set():
            self.p.raw = None

        assert_raises(AttributeError, _set)

    def test_raw_dir_property_ro(self):
        assert self.p.raw_dir == '/path'

        def _set():
            self.p.raw_dir = None

        assert_raises(AttributeError, _set)

    def test_filename_property_ro(self):
        assert self.p.filename == 'file_1234'

        def _set():
            self.p.filename = None

        assert_raises(AttributeError, _set)

    def test_seq_number_property_ro(self):
        assert self.p.seq_number == 1234

        def _set():
            self.p.seq_number = None

        assert_raises(AttributeError, _set)

    def test_tif_prop_returns_none(self):
        assert self.p.tif is None

    def test_tif_dir_prop_returns_none(self):
        assert self.p.tif_dir is None

    def test_exif_property(self):
        assert_is_instance(self.p.exif, exif)

        def _set():
            self.p.exif = None

        assert_raises(AttributeError, _set)

    def test_tif_dir_writeable(self):
        p = Photo('/path/file_1234.raw')
        p.tif_dir = '/tif/'

        assert p.tif_dir == '/tif'
        assert p.tif == '/tif/file_1234.tif'

    def test_default_data_property_ro(self):
        assert_is_instance(self.p.data, Maker)

        def _set():
            self.p.data = None

        assert_raises(AttributeError, _set)

    def test_is_bracketed_property_ro(self):
        assert self.p.is_bracketed is True

        def _set():
            self.p.is_bracketed = None

        assert_raises(AttributeError, _set)

    def test_bracket_value_property_ro(self):
        assert self.p.bracket_value == 0

        def _set():
            self.p.bracket_value = None

        assert_raises(AttributeError, _set)

    def test_bracket_count_property_ro(self):
        assert self.p.bracket_count == 3

        def _set():
            self.p.bracket_count = None

        assert_raises(AttributeError, _set)


class TestTifPhoto(object):
    
    def setUp(self):
        self.p = MockPhoto(tif='/tif/file_1234.tif')

    def teardown(self):
        pass

    def test_raw_property_returns_none(self):
        assert self.p.raw is None

    def test_raw_dir_property_returns_none(self):
        assert self.p.raw_dir is None

    def test_filename_property_returns_value(self):
        assert self.p.filename == 'file_1234'

    def test_seq_number_property_returns_value(self):
        assert self.p.seq_number == 1234

    def test_tif_property_returns_value(self):
        assert self.p.tif == '/tif/file_1234.tif'

    def test_tif_dir_property_returns_value(self):
        assert self.p.tif_dir == '/tif'

    def test_tif_dir_write_once(self):
        def _set():
            self.p.tif_dir = None
        assert_raises(ValueError, _set)

    def test_exif_property_returns_value(self):
        assert_is_instance(self.p.exif, exif)
