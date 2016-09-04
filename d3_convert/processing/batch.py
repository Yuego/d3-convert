# coding: utf-8
from __future__ import unicode_literals, absolute_import

import os

import shutil
import threading

from ..utils import cpus, makedirs
from ..utils.compat import Queue

from .commands import get_blend_filename
from .whitebalance import WhiteBalance
from .workers import blend_worker, convert_worker


class Batch(object):

    def __init__(self, *args, **kwargs):
        pass

    def process(self, src_photos, dstpath, force=False):
        raise NotImplementedError()


class BatchRAWConverter(Batch):
    photos = None

    def __init__(self, raw_format=None, dst_format=None, *args, **kwargs):
        super(BatchRAWConverter, self).__init__(*args, **kwargs)

        assert raw_format is None or raw_format in ['cr2'], 'Unknown RAW format: {0}'.format(raw_format)
        assert dst_format is None or dst_format in ['tif'], 'Unknown target images format: {0}'.format(dst_format)

        self.dst_format = dst_format or 'tif'
        self.wb = WhiteBalance()

    def set_wb_mode(self, mode, source=None):
        self.wb.setup(mode=mode)

    def gen_wb(self, photos):
        bracket_count = photos[0].bracket_count
        total_photos = len(photos)
        photo_number = (bracket_count // 2) + 1 if total_photos >= bracket_count else 0
        return self.wb.generate_for(photos[photo_number])

    def skip_already_converted(self, dstdir, photos):
        for photo in photos:
            dst_filename = os.path.join(dstdir, '{0}.{1}'.format(photo.name, self.dst_format))
            if not os.path.exists(dst_filename):
                yield photo

    def process(self, src_photos, dstpath, force=False):
        tiffs = []
        errors = []

        if force:
            shutil.rmtree(dstpath, ignore_errors=True)

        if src_photos:
            makedirs(dstpath, mode=0o775)

            queue = Queue()
            for photo in self.skip_already_converted(dstdir=dstpath, photos=src_photos):
                queue.put(photo)

            if not queue.empty():
                threads = [threading.Thread(
                    target=convert_worker,
                    kwargs=dict(
                        queue=queue,
                        dstpath=dstpath,
                        img_format=self.dst_format,
                        wb=self.gen_wb(src_photos),
                        tiffs=tiffs,
                        errors=errors,
                    ),
                ) for _ in range(cpus)]

                for thread in threads:
                    thread.setDaemon(True)
                    thread.start()

                for thread in threads:
                    thread.join()

        return tiffs


class BatchTIFFBlender(Batch):

    def check_sequence_numbers(self, batch, length):
        for i in range(0, length - 1):
                if batch[i].seq_number + 1 != batch[i+1].seq_number:
                    return False

        return True

    def get_blend_batches(self, tiff_photos):
        bracketed_photos = sorted([p for p in tiff_photos if p.is_bracketed],
                                  key=lambda p: p.seq_number)

        while bracketed_photos and len(bracketed_photos) > bracketed_photos[0].bracket_count - 1:
            bracket_count = bracketed_photos[0].bracket_count

            batch = bracketed_photos[0:bracket_count]

            if self.check_sequence_numbers(batch, bracket_count):
                ordered_batch = sorted([p for p in batch], key=lambda p: p.bracket_value, reverse=True)

                subs = []
                for j in range(0, bracket_count-1):
                    subs.append(ordered_batch[j].bracket_value - ordered_batch[j+1].bracket_value)

                if sum(subs) / len(subs) == subs[0]:
                    yield bracketed_photos[0: bracket_count]
                    bracketed_photos = bracketed_photos[bracket_count:]
                    continue

            bracketed_photos = bracketed_photos[1:]

    def check_already_blended(self, dstpath, batch):
        filename = get_blend_filename(dstpath=dstpath, batch=batch)
        filepath = os.path.join(dstpath, filename)
        return os.path.exists(filepath)

    def process(self, src_photos, dstpath, force=False):
        blends = []
        errors = []

        if force:
            shutil.rmtree(dstpath, ignore_errors=True)

        queue = Queue()

        for batch in self.get_blend_batches(tiff_photos=src_photos):
            if not self.check_already_blended(dstpath=dstpath, batch=batch):
                queue.put(batch)

        if not queue.empty():
            makedirs(dstpath, mode=0o775)

            threads = [threading.Thread(
                target=blend_worker,
                kwargs=dict(
                    queue=queue,
                    dstpath=dstpath,
                    blends=blends,
                    errors=errors,
                ),
            ) for _ in range(cpus)]

            for thread in threads:
                thread.setDaemon(True)
                thread.start()

            for thread in threads:
                thread.join()

        return blends
