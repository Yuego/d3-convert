#coding: utf-8
from __future__ import unicode_literals, absolute_import

from exiftool import ExifTool
import glob
from lxml import etree
import os
import scandir

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

import shutil
import threading


from .commands import convert_to_cmd, get_wb_cmd
from .exceptions import *
from .lock import is_locked
from .log import log
from .photo2 import Photo
from .process import Process
from .utils import cpus, makedirs


def convert_worker(queue, dstdir, img_format, wb=None):
    while True:
        try:
            photo = queue.get(False)
        except Empty:
            return

        log.debug('Обработка файла: {0}'.format(photo.filename))
        cmd = convert_to_cmd(dstdir=dstdir, img_format=img_format, filename=photo.filename, wb=wb)
        p = Process(cmd, cwd=dstdir)
        p.run()

        result = ' '.join([p.result, p.errors]).lower()
        if 'saved' in result:
            log.debug('`{0}` сконвертирован в каталог: {1}'.format(photo.filename, dstdir))
        elif 'error' in result:
            log.error('`{0}` не сконвертирован из-за ошибки:\n\r {1}'.format(photo.filename, result))
        log.progress()


class WhiteBalance(object):

    def __init__(self):
        self.mode = 'camera'
        self.filename = None

    def gen_camera_wb(self, **kwargs):
        return ['--wb=camera']

    def gen_manual_wb(self, photo=None, source=None, **kwargs):
        temp = None
        green = None

        if photo is not None:
            source = photo.dirname

        if os.path.isfile(source):
            config_files = [source]
        elif os.path.isdir(source):
            config_files = glob.glob(os.path.join(source, '*.ufraw'))
        else:
            raise ValueError('Unknown UFRAW config source: {0}'.format(source))

        for config_path in config_files:
            doc = etree.parse(config_path)
            temp = doc.find('Temperature')
            green = doc.find('Green')

            if temp is not None and green is not None:
                break

        if not temp or not green:
            raise ValueError('WhiteBalance settings file not found in `{0}`'.format(source))

        return [
            '--temperature={0}'.format(temp.text),
            '--green={0}'.format(green.text)
        ]

    def gen_auto_wb(self, photo, **kwargs):
        output = os.path.join(photo.dirname, 'wb')
        cmd = get_wb_cmd(src_file=photo.filename, dst_file=output)

        proc = Process(cmd, cwd=photo.dirname)
        proc.run()
        proc.wait()

        config_path = os.path.join(photo.dirname, 'wb.ufraw')
        result = self.gen_manual_wb(source=config_path)

        os.unlink(config_path)

        return result

    def setup(self, mode, filename=None):
        assert mode in ['auto', 'camera', 'manual'], 'Unknown WhiteBalance mode: {0}'.format(mode)

        self.mode = mode
        self.filename = filename

    def generate_for(self, photo):
        return getattr(self, 'gen_{0}_wb'.format(self.mode))(photo=photo, source=self.filename)


class DirectoryRAWConverter(object):
    photos = None

    def __init__(self, raw_format=None, dst_dirname=None, dst_format=None):
        assert raw_format is None or raw_format in ['cr2'], 'Unknown RAW format: {0}'.format(raw_format)
        assert dst_format is None or dst_format in ['tif'], 'Unknown target images format: {0}'.format(dst_format)

        self.dst_dirname = dst_dirname or 'tiff'
        self.src_format = raw_format or 'cr2'
        self.dst_format = dst_format or 'tif'
        self.wb = WhiteBalance()

    def set_wb_mode(self, mode, source=None):
        self.wb.setup(mode=mode, source=source)

    def collect_raw(self, path, filenames):
        cr2_files = []

        with ExifTool() as et:
            for fn in filenames:
                filename, _, ext = fn.lower().rpartition('.')
                if ext == self.src_format:
                    fullpath = os.path.join(path, fn)

                    try:
                        photo = Photo(fullpath, exiftool_instance=et)
                    except (InvalidFile, UnknownCamera) as e:
                        raise

                    cr2_files.append(photo)

        return cr2_files

    def gen_wb(self, photos):
        bracket_count = photos[0].bracket_count
        total_photos = len(photos)
        photo_number = (bracket_count // 2) + 1 if total_photos >= bracket_count else 0
        return self.wb.generate_for(photos[photo_number])

    def check_already_converted(self, dstdir, photos):
        new_photos = list()
        for photo in photos:
            dst_filename = os.path.join(dstdir, '{0}.{1}'.format(photo.name, self.dst_format))
            if not os.path.exists(dst_filename):
                new_photos.append(photo)

        return new_photos

    def convert(self, path, filenames, force=False):
        dstdir = os.path.join(path, self.dst_dirname)

        if force:
            shutil.rmtree(dstdir, ignore_errors=True)

        makedirs(dstdir, mode=0o775)

        photos = self.collect_raw(path, filenames=filenames)
        self.check_already_converted(dstdir=dstdir, photos=photos)

        if photos:
            queue = Queue()
            for photo in photos:
                queue.put(photo)

            threads = [threading.Thread(
                target=convert_worker,
                kwargs=dict(
                    queue=queue,
                    dstdir=dstdir,
                    img_format=self.dst_format,
                    wb=self.gen_wb(photos),
                ),
            ) for _i in range(cpus)]

            for thread in threads:
                thread.setDaemon(True)
                thread.start()

            for thread in threads:
                thread.join()


class WalkRAWConverter(object):

    def __init__(self, dst_dirname=None, wb_mode=None, wb_source=None):
        self.dir_converter = DirectoryRAWConverter(dst_dirname=dst_dirname)
        self.dir_converter.set_wb_mode(wb_mode)


    def convert(self, src_dir, force=False):
        for (srcpath, dirs, files) in scandir.walk(src_dir):

            if is_locked(src_dir, srcpath, 'ufraw-batch') or is_locked(src_dir, srcpath, 'enfuse'):
                log.status = 'Каталог `{0}` уже обрабатывается другой копией конвертера. Пропускаем'.format(srcpath)
                continue

            self.dir_converter.convert(path=srcpath, filenames=files, force=force)
