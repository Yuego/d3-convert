# coding: utf-8
from __future__ import unicode_literals, absolute_import


from .batch import BatchTIFFBlender
from .processor import ImageProcessor, DirectoryImageProcessorMixin, RecursiveImageProcessorMixin


class TIFFBlender(ImageProcessor):
    batch_class = BatchTIFFBlender


class DirectoryTIFFBlender(TIFFBlender, DirectoryImageProcessorMixin):
    pass


class RecursiveTIFFBlender(TIFFBlender, RecursiveImageProcessorMixin):
    pass
