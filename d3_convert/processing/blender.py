# coding: utf-8
from __future__ import unicode_literals, absolute_import


from .batch import BatchTIFFBlender
from .processor import (
    ImageProcessor,
    DirectoryImageProcessorMixin,
    RecursiveImageProcessorMixin
)


class TIFFBlender(ImageProcessor):
    default_src_format = 'tif'
    default_dst_dirname = 'blend'
    batch_class = BatchTIFFBlender


class DirectoryTIFFBlender(DirectoryImageProcessorMixin, TIFFBlender):
    pass


class RecursiveTIFFBlender(RecursiveImageProcessorMixin, TIFFBlender):
    pass
