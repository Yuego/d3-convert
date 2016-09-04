# coding: utf-8
from __future__ import unicode_literals, absolute_import

from exiftool import ExifTool
import os
import scandir


from ..exceptions import *
from ..log import log
from ..photo import Photo

from .batch import Batch
from .lock import is_locked


class ImageProcessor(object):
    default_src_format = 'cr2'
    default_dst_dirname = 'tiff'
    batch_class = Batch

    def __init__(self, src_format=None, dst_dirname=None, protect_dirs=None, **kwargs):
        self.src_format = src_format or self.default_src_format
        self.dst_dirname = dst_dirname or self.default_dst_dirname

        self.protected_dirs = [
            self.dst_dirname,
        ]
        if protect_dirs and isinstance(protect_dirs, (list, tuple)):
            self.protected_dirs.extend(protect_dirs)

        self.batch = self.batch_class()

    def collect_photos(self, path, filenames):
        photo_files = []

        with ExifTool() as et:
            for fn in filenames:
                filename, _, ext = fn.lower().rpartition('.')
                if ext == self.src_format:
                    fullpath = os.path.join(path, fn)

                    try:
                        photo = Photo(fullpath, metadata=et.get_metadata(fullpath))
                    except (InvalidFile, UnknownCamera) as e:
                        raise

                    photo_files.append(photo)

        return photo_files

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

    def next_dir(self, srcpath, dst_dirname, is_locked_func):
        raise NotImplementedError()

    def process(self, src, force=False):
        for (srcpath, dstpath, filenames) in self.next_dir(srcpath=src,
                                                           dst_dirname=self.dst_dirname,
                                                           is_locked_func=self.is_locked):

            photos = self.collect_photos(srcpath, filenames=filenames)

            result = self.batch.process(src_photos=photos, dstpath=dstpath, force=force)
            if result:
                yield result


class DirectoryImageProcessorMixin(object):

    def next_dir(self, srcpath, dst_dirname, is_locked_func):
        dstpath = os.path.join(srcpath, dst_dirname)
        if not is_locked_func(srcpath=srcpath, dstpath=dstpath):
            filenames = [f for f in scandir.listdir(srcpath) if os.path.isfile(os.path.join(srcpath, f))]
            if filenames:
                yield srcpath, dstpath, filenames


class RecursiveImageProcessorMixin(object):

    def next_dir(self, srcpath, dst_dirname, is_locked_func):
        for (srcpath, _, filenames) in scandir.walk(srcpath, followlinks=False):
            dstpath = os.path.join(srcpath, dst_dirname)

            if filenames and not is_locked_func(srcpath=srcpath, dstpath=dstpath):
                yield srcpath, dstpath, filenames
