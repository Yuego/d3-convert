# coding: utf-8
from __future__ import unicode_literals, absolute_import

from abc import ABCMeta, abstractmethod
from exiftool import ExifTool
import os
import scandir

from ..exceptions import *
from ..log import log
from ..photo import Photo
from ..utils.lock import is_locked

from .batch import Batch


class ImageProcessorInterface(object, metaclass=ABCMeta):
    default_src_format = 'cr2'
    default_dst_dirname = 'tiff'
    batch_class = Batch
    src_format = None
    dst_dirname = None
    protected_dirs = []
    batch = None

    @abstractmethod
    def collect_photos(self, path, filenames, mixed=False):
        """
        Получает список объектов Photo и его наследников
        из каталога path согласно списку filenames
        :param path: str
        :param filenames: list
        :param mixed: bool
        :return: list
        """

    @abstractmethod
    def get_dstpath(self, srcpath, dst_dirname):
        """
        Вычисляет путь назначения для сохранения обработанных изображений
        :param srcpath: str
        :param dst_dirname: str
        :return: str
        """

    @abstractmethod
    def next_dir(self, srcpath, dst_dirname, is_locked_func):
        """
        Итератор по обрабатываемым каталогам
        :param srcpath: str
        :param dst_dirname: str
        :param is_locked_func: function
        :return: tuple(srcpath, dstpath, filenames)
        """

    @abstractmethod
    def process(self, src, force=False, clear=False):
        """
        Точка входа в процессор. Запускает обработку каталога src
        Возвращает список результирующих изображений
        :param src: str or list
        :param force: bool
        :param clear: bool
        :return: list
        """


class ImageProcessor(ImageProcessorInterface):

    def __init__(self, src_format=None, dst_dirname=None, protect_dirs=None, **kwargs):
        self.src_format = src_format or self.default_src_format
        self.dst_dirname = dst_dirname or self.default_dst_dirname

        self.protected_dirs = [
            self.dst_dirname,
        ]
        if protect_dirs and isinstance(protect_dirs, (list, tuple)):
            self.protected_dirs.extend(protect_dirs)

        self.batch = self.batch_class()

    def collect_photos(self, path, filenames, mixed=False):
        photo_files = []

        with ExifTool() as et:
            for fn in filenames:
                filename, _, ext = fn.lower().rpartition('.')
                if mixed or ext == self.src_format:
                    fullpath = os.path.join(path, fn)

                    try:
                        photo = Photo(fullpath, metadata=et.get_metadata(fullpath))
                    except (InvalidFile, UnknownCamera) as e:
                        log.warning('Не могу прочесть EXIF из {0}. Пробуем JPG'.format(fullpath))
                        # FallBack to JPG
                        for _fn in filenames:
                            _filename, _, _ext = _fn.lower().rpartition('.')
                            if ext == 'jpg':
                                _fullpath = os.path.join(path, fn)
                                try:
                                    photo = Photo(_fullpath, metadata=et.get_metadata(_fullpath))
                                except (InvalidFile, UnknownCamera):
                                    log.warning('JPG из {0} тоже не получилось. Пропускаем...'.format(_fullpath))
                                else:
                                    photo_files.append(photo)
                                    break
                    else:
                        photo_files.append(photo)

        return list(set(photo_files))

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

    def get_dstpath(self, srcpath, dst_dirname):
        return os.path.join(srcpath, dst_dirname)

    def process(self, src, force=False, clear=False):
        for (srcpath, dstpath, filenames) in self.next_dir(srcpath=src,
                                                           dst_dirname=self.dst_dirname,
                                                           is_locked_func=self.is_locked):

            photos = self.collect_photos(srcpath, filenames=filenames, mixed=False)
            result = self.batch.process(src_photos=photos, dstpath=dstpath, force=force, clear=clear)
            if result:
                yield result


class SingleImageProcessorMixin(ImageProcessorInterface):

    def next_dir(self, srcpath, dst_dirname, is_locked_func):
        filename = os.path.basename(srcpath)
        dirname = os.path.dirname(srcpath)
        dstpath = os.path.join(dirname, dst_dirname)
        if not is_locked_func(srcpath=dirname, dstpath=dstpath):
            yield dirname, dstpath, [filename]


class MultipleImagesProcessingMixin(ImageProcessorInterface):

    def process(self, src, force=False, clear=False):
        srcs = [os.path.dirname(s) for s in src]
        assert srcs and all([s == srcs[0] for s in srcs]), 'Files from different directories!'

        srcpath = srcs[0]
        dstpath = self.get_dstpath(srcpath=srcpath, dst_dirname=self.dst_dirname)
        filenames = [os.path.basename(s) for s in src]

        photos = self.collect_photos(srcpath, filenames=filenames, mixed=True)
        result = self.batch.process(src_photos=photos, dstpath=dstpath, force=force, clear=clear)
        if result:
            yield result


class DirectoryImageProcessorMixin(ImageProcessorInterface):

    def next_dir(self, srcpath, dst_dirname, is_locked_func):
        dstpath = self.get_dstpath(srcpath=srcpath, dst_dirname=dst_dirname)
        if not is_locked_func(srcpath=srcpath, dstpath=dstpath):
            filenames = [f for f in scandir.listdir(srcpath) if os.path.isfile(os.path.join(srcpath, f))]
            if filenames:
                yield srcpath, dstpath, filenames


class RecursiveImageProcessorMixin(ImageProcessorInterface):

    def next_dir(self, srcpath, dst_dirname, is_locked_func):
        for (srcpath, _, filenames) in scandir.walk(srcpath, followlinks=False):
            dstpath = dstpath = self.get_dstpath(srcpath=srcpath, dst_dirname=dst_dirname)

            if filenames and not is_locked_func(srcpath=srcpath, dstpath=dstpath):
                yield srcpath, dstpath, filenames
