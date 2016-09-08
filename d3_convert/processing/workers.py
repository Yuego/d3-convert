# coding: utf-8
from __future__ import unicode_literals, absolute_import

import os

from ..utils.compat import Empty
from ..utils.process import Process
from ..log import log
from ..photo import BlendPhoto, TiffPhoto
from .commands import blend_to_cmd, convert_jpg_to_cmd, convert_to_cmd, get_blend_filename


remove_metadata_convert = (
    'EXIF:Orientation',
)
remove_metadata_blend = remove_metadata_convert + (
    'EXIF:Compression',
)


def blend_worker(queue, dstpath, processed, errors, **kwargs):
    while True:
        try:
            batch = queue.get(False)
        except Empty:
            return

        blend_filename = get_blend_filename(dstpath=dstpath, batch=batch)
        blend_cmd = blend_to_cmd(dst_filename=blend_filename, batch=batch)
        p = Process(blend_cmd, cwd=dstpath)
        p.run()

        result = ' '.join([p.result, p.errors]).lower()
        if True or 'error' not in result:
            batch_len = len(batch)
            half_batch = batch_len // 2
            if not batch_len % 2 == 0:
                half_batch += 1

            blend = BlendPhoto(filename=blend_filename, metadata=batch[half_batch], exclude_tags=remove_metadata_blend)

            processed.append(blend)
        else:
            log.warning('Can`t blend files: {0}'.format(repr(batch)))
            log.warning('ERROR: {0}'.format(result))
        log.progress()


def convert_worker(queue, dstpath, img_format, processed, errors, wb=None, force=False, **kwargs):
    while True:
        try:
            photo = queue.get(False)
        except Empty:
            return

        log.debug('Обработка файла: {0}'.format(photo.filename))
        if photo.type == 'jpg':
            dst_filename = os.path.join(dstpath, '{0}.{1}'.format(photo.name, img_format))
            cmd = convert_jpg_to_cmd(src_filename=photo.filename, dst_filename=dst_filename)
        else:
            cmd = convert_to_cmd(dstdir=dstpath, img_format=img_format, filename=photo.filename, wb=wb, force=force)
        p = Process(cmd, cwd=dstpath)
        p.run()

        result = ' '.join([p.result, p.errors]).lower()
        if 'saved' in result or not result.strip():
            log.debug('`{0}` сконвертирован в каталог: {1}'.format(photo.filename, dstpath))
            tiff_filename = os.path.join(dstpath, '{0}.tif'.format(photo.name))

            tiff = TiffPhoto(filename=tiff_filename, metadata=photo, exclude_tags=remove_metadata_convert)

            processed.append(tiff)

        elif 'error' in result:
            log.error('`{0}` не сконвертирован из-за ошибки:\n\r {1}'.format(photo.filename, result))
        log.progress()
