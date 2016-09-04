#coding: utf-8
from __future__ import unicode_literals, absolute_import

from .batch import BatchRAWConverter
from .processor import (
    ImageProcessor,
    SingleImageProcessorMixin,
    DirectoryImageProcessorMixin,
    RecursiveImageProcessorMixin,
)


class RAWConverter(ImageProcessor):
    batch_class = BatchRAWConverter

    def __init__(self,
                 src_format=None, dst_dirname=None, protect_dirs=None,
                 wb_mode=None, wb_source=None, *args, **kwargs):
        super(RAWConverter, self).__init__(src_format=src_format,
                                           dst_dirname=dst_dirname,
                                           protect_dirs=protect_dirs, **kwargs)

        self.batch.set_wb_mode(wb_mode)


class SingleRAWConverter(SingleImageProcessorMixin, RAWConverter):
    pass


class DirectoryRAWConverter(DirectoryImageProcessorMixin, RAWConverter):
    pass


class RecursiveRAWConverter(RecursiveImageProcessorMixin, RAWConverter):
    pass


