# coding: utf-8
from __future__ import unicode_literals, absolute_import

import os

from .commands import blend_to_cmd, convert_to_cmd, get_blend_filename
from .compat import Empty
from .log import log
from .photo2 import BlendPhoto, TiffPhoto
from .process import Process


remove_metadata = [
    'EXIF:Compression',
    'EXIF:Orientation',
]


def blend_worker(queue, dstdir, blends, errors):
    while True:
        try:
            batch = queue.get(False)
        except Empty:
            return

        blend_filename = get_blend_filename(dstdir=dstdir, batch=batch)
        blend_cmd = blend_to_cmd(dst_filename=blend_filename, batch=batch)
        p = Process(blend_cmd, cwd=dstdir)

        result = ' '.join([p.result, p.errors]).lower()
        if 'error' not in result:
            batch_len = len(batch)
            half_batch = batch_len // 2
            if not batch_len % 2 == 0:
                half_batch += 1

            metadata = batch[half_batch].get_metadata()
            for rm in remove_metadata:
                metadata.pop(rm, None)

            blend = BlendPhoto(filename=blend_filename, metadata=metadata)
            blend.save_metadata()

            blends.append(blend)
        else:
            pass


def convert_worker(queue, dstpath, img_format, tiffs, errors, wb=None):
    while True:
        try:
            photo = queue.get(False)
        except Empty:
            return

        log.debug('Обработка файла: {0}'.format(photo.filename))
        cmd = convert_to_cmd(dstdir=dstpath, img_format=img_format, filename=photo.filename, wb=wb)
        p = Process(cmd, cwd=dstpath)
        p.run()

        result = ' '.join([p.result, p.errors]).lower()
        if 'saved' in result:
            log.debug('`{0}` сконвертирован в каталог: {1}'.format(photo.filename, dstpath))
            tiff_filename = os.path.join(dstpath, '{0}.tif'.format(photo.name))
            tiff = TiffPhoto(filename=tiff_filename, metadata=photo.get_metadata())
            tiffs.append(tiff)

        elif 'error' in result:
            log.error('`{0}` не сконвертирован из-за ошибки:\n\r {1}'.format(photo.filename, result))
        log.progress()

