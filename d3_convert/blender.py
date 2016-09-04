# coding: utf-8
from __future__ import unicode_literals, absolute_import

import os
import shutil
import threading

from .commands import get_blend_filename
from .compat import Queue
from .utils import cpus
from .workers import blend_worker


class BatchTIFFBlender(object):

    def get_blend_batches(self, tiff_photos):
        bracketed_photos = sorted([p for p in tiff_photos if p.is_bracketed],
                                  key=lambda p: p.seq_number)

        while len(bracketed_photos) > bracketed_photos[0].bracket_count - 1:
            bracket_count = bracketed_photos[0].bracket_count

            batch = bracketed_photos[0:bracket_count]

            ordered_batch = sorted([p for p in batch], key=lambda p: p.bracket_value, reverse=True)

            subs = []
            for j in range(0, bracket_count):
                subs.append(ordered_batch[j].bracket_value - ordered_batch[j+1].bracket_value)

            if sum(subs) / len(subs) == subs[0]:
                yield bracketed_photos[0: bracket_count]
                bracketed_photos = bracketed_photos[bracket_count:]

            bracketed_photos = bracketed_photos[1:]

    def check_already_blended(self, dstpath, batch):
        filename = get_blend_filename(dstpath=dstpath, batch=batch)
        filepath = os.path.join(dstpath, filename)
        return os.path.exists(filepath)

    def blend(self, tiff_photos, dstpath, force=False):
        blends = []
        errors = []

        if force:
            shutil.rmtree(dstpath, ignore_errors=True)

        queue = Queue()

        for batch in self.get_blend_batches(tiff_photos=tiff_photos):
            if not self.check_already_blended(dstpath=dstpath, batch=batch):
                queue.put(batch)

        if not queue.empty():
            threads = [threading.Thread(
                target=blend_worker,
                kwargs=dict(
                    queue=queue,
                    dstdir=dstpath,
                    blends=blends,
                    errors=errors,
                ),
            ) for _i in range(cpus)]

            for thread in threads:
                thread.setDaemon(True)
                thread.start()

            for thread in threads:
                thread.join()

        return blends


class DirectoryTIFFBlender(object):

    def __init__(self, src_format=None, dst_dirname=None, protect_dirs=None):
        self.src_format = src_format or 'tif'
        self.dst_dirname = dst_dirname or 'blend'

        self.blender = BatchTIFFBlender()

        self.protected_dirs = [
            self.dst_dirname,
        ]
        if protect_dirs and isinstance(protect_dirs, (list, tuple)):
            self.protected_dirs.extend(protect_dirs)
