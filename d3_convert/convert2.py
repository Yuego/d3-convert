#coding: utf-8
from __future__ import unicode_literals, absolute_import

from exiftool import ExifTool
import glob
from lxml import etree
import io
import os

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

import shutil
import threading


from .commands import convert_to_tiff_cmd, get_wb_cmd
from .exceptions import *
from .log import log
from .photo2 import Photo
from .process import Process
from .utils import cpus, makedirs


def get_wb(photo, wb):
    result = []
    if wb == 'camera':
        result = ['--wb=camera']

    if wb == 'auto':
        output = os.path.join(photo.dirname, 'img')
        cmd = get_wb_cmd(src_file=photo.filename, dst_file=output)

        proc = Process(cmd, cwd=photo.dirname)
        proc.run()
        proc.wait()

    if wb in ['auto', 'manual']:
        config_files = glob.glob(os.path.join(photo.dirname, '*.ufraw'))

        for config in config_files:
            doc = etree.parse(config)
            temp = doc.find('Temperature')
            green = doc.find('Green')

            if temp is not None and green is not None:
                result = [
                    '--temperature={0}'.format(temp.text),
                    '--green={0}'.format(green.text),
                ]

            if wb == 'auto':
                os.unlink(config)

            if result:
                break

        if not config_files or not result:
            raise ValueError('WhiteBalance settings file not found in dir `{0}`'.format(photo.dirname))

    return result

def convert_cr2(photos, dstdir, force=False):
    if force:
        shutil.rmtree(dstdir, ignore_errors=True)

    makedirs(dstdir, mode=0o775)

    source_file = os.path.join(dstdir, '.source')
    with io.open(source_file, 'w') as f:
        f.write(photos[0].dirname)

    base_cmd = convert_to_tiff_cmd(dstdir=dstdir)
    base_cmd.extend(get_wb(photos, autowb, nowb))

    q = Queue()
    for p in photos:
        q.put(p)

    results = {
        'converted': [],
        'errors': [],
    }

    def worker():
        while True:
            try:
                photo = q.get(False)
            except Empty:
                return

            log.debug('Обработка файла `{0}`'.format(photo.raw))
            cmd = base_cmd[:]
            cmd.append(photo.raw)
            p = Process(cmd, cwd=dstdir)
            p.run()


            result = ' '.join([p.result, p.errors]).lower()
            if 'saved' in result:
                log.debug('`{0}` сконвертирован в `{1}`'.format(photo.raw, photo.tif))
            elif 'error' in result:
                log.error('`{0}` не сконвертирован из-за ошибки:\n\r {1}'.format(photo.raw, result))
            log.progress()

    threads = [threading.Thread(target=worker) for _i in range(cpus)]

    for thread in threads:
        thread.setDaemon(True)
        thread.start()

    for thread in threads:
        thread.join()

    if not results['errors']:
        log.status = 'Каталог `{0}` сконвертирован'.format(photos[0].raw_dir)
    else:
        log.status = 'Каталог `{0}` сконвертирован с ошибками'.format(photos[0].raw_dir)
        log.warning(repr(results))

    return results


def collect_cr2(dirname, filelist):
    with ExifTool() as et:
        cr2_files = []
        for file in filelist:
            filename, _, ext = file.lower().rpartition('.')
            if ext == 'cr2':
                filename = os.path.join(dirname, file)

                try:
                    photo = Photo(filename, exiftool_instance=et)
                except (InvalidFile, UnknownCamera) as e:
                    raise

                cr2_files.append(photo)
        return cr2_files
