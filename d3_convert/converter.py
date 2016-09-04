#coding: utf-8
from __future__ import unicode_literals, absolute_import

from exiftool import ExifTool
import os
import scandir

import shutil
import threading

from .compat import Queue
from .exceptions import *
from .lock import is_locked
from .log import log
from .photo2 import Photo
from .utils import cpus, makedirs
from .whitebalance import WhiteBalance
from .workers import convert_worker


class BatchRAWConverter(object):
    photos = None

    def __init__(self, raw_format=None, dst_format=None):
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

    def convert(self, raw_photos, dstpath, force=False):
        tiffs = []
        errors = []

        if force:
            shutil.rmtree(dstpath, ignore_errors=True)

        if raw_photos:
            makedirs(dstpath, mode=0o775)

            queue = Queue()
            for photo in self.skip_already_converted(dstdir=dstpath, photos=raw_photos):
                queue.put(photo)

            if not queue.empty():
                threads = [threading.Thread(
                    target=convert_worker,
                    kwargs=dict(
                        queue=queue,
                        dstdir=dstpath,
                        img_format=self.dst_format,
                        wb=self.gen_wb(raw_photos),
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


class DirectoryRAWConverter(object):

    def __init__(self, src_format=None, dst_dirname=None, wb_mode=None, wb_source=None, protect_dirs=None):
        self.src_format = src_format or 'cr2'
        self.dst_dirname = dst_dirname or 'tiff'

        self.converter = BatchRAWConverter()
        self.converter.set_wb_mode(wb_mode)

        self.protected_dirs = [
            self.dst_dirname,
        ]
        if protect_dirs and isinstance(protect_dirs, (list, tuple)):
            self.protected_dirs.extend(protect_dirs)

    def collect_photos(self, path, filenames):
        cr2_files = []

        with ExifTool() as et:
            for fn in filenames:
                filename, _, ext = fn.lower().rpartition('.')
                if ext == self.src_format:
                    fullpath = os.path.join(path, fn)

                    try:
                        photo = Photo(fullpath, metadata=et.get_metadata(fullpath))
                    except (InvalidFile, UnknownCamera) as e:
                        raise

                    cr2_files.append(photo)

        return cr2_files

    def is_locked(self, srcpath, dstpath):
        result = False
        name = os.path.basename(srcpath)
        if name in self.protected_dirs:
            log.debug('Пропуск служебного каталога: {0}'.format(srcpath))
            result = True

        if is_locked(srcpath, dstpath, 'ufraw-batch') or is_locked(srcpath, dstpath, 'enfuse'):
            log.status = 'Каталог `{0}` уже обрабатывается другой копией конвертера. Пропускаем'.format(srcpath)
            result = True

        return result

    def next_dir(self, srcpath):
        dstpath = os.path.join(srcpath, self.dst_dirname)
        if not self.is_locked(srcpath=srcpath, dstpath=dstpath):
            filenames = [f for f in scandir.listdir(srcpath) if os.path.isfile(f)]
            if filenames:
                yield srcpath, dstpath, filenames

    def convert(self, src, force=False):
        for (srcpath, dstpath, filenames) in self.next_dir(srcpath=src):
            photos = self.collect_photos(srcpath, filenames=filenames)

            tiffs = self.converter.convert(raw_photos=photos, dstpath=dstpath, force=force)
            if tiffs:
                yield tiffs


class RecursiveRAWConverter(DirectoryRAWConverter):

    def next_dir(self, srcpath):
        for (srcpath, _, filenames) in scandir.walk(srcpath, followlinks=False):
            dstpath = os.path.join(srcpath, self.dst_dirname)

            if filenames and not self.is_locked(srcpath=srcpath, dstpath=dstpath):
                yield srcpath, dstpath, filenames
