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
    src_format = None
    dst_format = None

    def __init__(self, src_format=None, dst_format=None, *args, **kwargs):
        self.src_format = src_format or self.src_format
        self.dst_format = dst_format or self.dst_format

    def get_queue(self, photos, dstpath, force=False, **kwargs):
        return Queue()

    def get_threads_count(self, photos):
        return cpus

    def get_worker_func(self):
        raise NotImplementedError()

    def get_worker_kwargs(self, photos, **kwargs):
        return {}

    def process(self, src_photos, dstpath, force=False, clear=False):
        processed = []
        errors = []

        if clear:
            shutil.rmtree(dstpath, ignore_errors=True)

        queue = self.get_queue(photos=src_photos, dstpath=dstpath, force=force)
        if not queue.empty():
            makedirs(dstpath, mode=0o775)

            worker_kwargs = dict(
                queue=queue,
                processed=processed,
                errors=errors,
                dstpath=dstpath,
                force=force,
            )
            worker_kwargs.update(self.get_worker_kwargs(photos=src_photos))

            threads = [threading.Thread(
                target=self.get_worker_func(),
                kwargs=worker_kwargs,
            ) for _ in range(self.get_threads_count(photos=src_photos))]

            for thread in threads:
                thread.setDaemon(True)
                thread.start()

            for thread in threads:
                thread.join()

        return processed


class BatchRAWConverter(Batch):
    src_format = 'cr2'
    dst_format = 'tif'

    def __init__(self, src_format=None, dst_format=None, *args, **kwargs):
        super(BatchRAWConverter, self).__init__(*args, **kwargs)
        self.wb = WhiteBalance()

    def set_wb_mode(self, mode, source=None):
        self.wb.setup(mode=mode)

    def gen_wb(self, photos):
        bracket_count = photos[0].bracket_count
        total_photos = len(photos)
        photo_number = (bracket_count // 2) + 1 if total_photos >= bracket_count else 0
        return self.wb.generate_for(photos[photo_number])

    def skip_already_processed(self, dstpath, photos):
        for photo in photos:
            dst_filename = os.path.join(dstpath, '{0}.{1}'.format(photo.name, self.dst_format))
            if not os.path.exists(dst_filename):
                yield photo

    def get_worker_func(self):
        return convert_worker

    def get_worker_kwargs(self, photos, **kwargs):
        kwargs.update(dict(
            wb=self.gen_wb(photos=photos),
            img_format=self.dst_format,
        ))

        return kwargs

    def get_queue(self, photos, dstpath, force=False, **kwargs):
        queue = super(BatchRAWConverter, self).get_queue(photos=photos, dstpath=dstpath)

        if force:
            prepared = photos
        else:
            prepared = self.skip_already_processed(dstpath=dstpath, photos=photos)
        for photo in prepared:
            queue.put(photo)

        return queue


class BatchTIFFBlender(Batch):
    src_format = 'tif'
    dst_format = 'tif'

    def check_sequence_numbers(self, batch, length):
        for i in range(0, length - 1):
                if batch[i].seq_number + 1 != batch[i+1].seq_number:
                    return False

        return True

    def check_ndb_bracketing(self, batch, length):
        """
        Normal -> Dark -> Bright
        :param batch: list
        :param length: int
        :return: bool
        """
        half_len = length // 2
        first_half = batch[0:half_len + 1]
        second_half = batch[::-1][0:half_len + 1]

        first_subs = []
        second_subs = []
        for i in range(0, half_len - 1):
            first_subs.append(first_half[i + 1].bracket_value - first_half[i].bracket_value)
            second_subs.append(second_half[i].bracket_value - second_half[i + 1].bracket_value)
        return first_subs == second_subs

    def check_dnb_bracketing(self, batch, length):
        """
        Dark -> Normal -> Bright
        :param batch: list
        :param length: int
        :return: bool
        """
        return True

    def get_blend_batches(self, tiff_photos):
        bracketed_photos = sorted([p for p in tiff_photos if p.is_bracketed],
                                  key=lambda p: p.seq_number)

        while bracketed_photos and len(bracketed_photos) > bracketed_photos[0].bracket_count - 1:
            bracket_count = bracketed_photos[0].bracket_count

            batch = bracketed_photos[0:bracket_count]

            seq = self.check_sequence_numbers(batch, bracket_count)
            ndb = self.check_ndb_bracketing(batch, bracket_count)
            dnb = self.check_dnb_bracketing(batch, bracket_count)
            if seq and ndb and dnb:
                yield bracketed_photos[0:bracket_count]
                bracketed_photos = bracketed_photos[bracket_count:]
                continue

            bracketed_photos = bracketed_photos[1:]

    def check_already_processed(self, dstpath, photos):
        filename = get_blend_filename(dstpath=dstpath, batch=photos)
        filepath = os.path.join(dstpath, filename)
        return os.path.exists(filepath)

    def get_threads_count(self, photos):
        bracket_count = 1
        for photo in photos:
            if photo.is_bracketed:
                bracket_count = photo.bracket_count
                break
                
        return (cpus // bracket_count) * 2

    def get_worker_func(self):
        return blend_worker

    def get_queue(self, photos, dstpath, force=False, **kwargs):
        queue = super(BatchTIFFBlender, self).get_queue(photos=photos, dstpath=dstpath)

        for batch in self.get_blend_batches(tiff_photos=photos):
            if force or not self.check_already_processed(dstpath=dstpath, photos=batch):
                queue.put(batch)

        return queue
