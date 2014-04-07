#coding: utf-8
from __future__ import unicode_literals, absolute_import

from d3_convert.log import log
from d3_convert.photo import TifPhoto
from d3_convert.process import Process
from d3_convert.utils import cpus, makedirs

import os
import scandir
import shutil
import threading
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

_exif_clear = [
    'Exif.Image.Compression',
    'Exif.Image.Orientation',
    'Exif.Image2.Compression',
    'Exif.Image3.Compression',
]


def check_bracketing(photos):
    result = []

    bracketed_photos = sorted([p for p in photos if p.is_bracketed],
                              key=lambda p: p.seq_number)

    #TODO: добавить поддержку длинных последовательностей (5, 7, .. фото) брекетинга
    while len(bracketed_photos) > 2:
        p1, p2, p3 = bracketed_photos[0:3]

        # Верная последовательность
        if (p1.seq_number + 1 == p2.seq_number and p2.seq_number + 1 == p3.seq_number):
            # Средний - Тёмный - Светлый или Тёмный - Средний - Светлый
            if (p1.bracket_value - p2.bracket_value == p3.bracket_value - p1.bracket_value or
                    p2.bracket_value - p1.bracket_value == p3.bracket_value - p2.bracket_value):

                result.append([p1, p2, p3])

                bracketed_photos = bracketed_photos[3:]
                continue

        bracketed_photos = bracketed_photos[1:]

    return result


def blend_tif(photos, tif_dir, force=False):
    dst = os.path.join(tif_dir, 'blend')
    blend_file = os.path.join(dst, '.blend')
    if force:
        shutil.rmtree(dst, ignore_errors=True)

    makedirs(dst, mode=0o775)
    if os.path.exists(blend_file):
        return

    base_cmd = [
        'enfuse',
        '--compression=deflate',
        '-o',
    ]

    log.status = 'Сведение файлов в директории `{0}`'.format(tif_dir)

    bracketed = check_bracketing(photos)

    q = Queue()
    for b in bracketed:
        q.put(b)

    results = {
        'blended': [],
        'errors': [],
    }

    def worker():
        while True:
            try:
                br = q.get(False)
            except Empty:
                return

            dst_ = ['IMG',]
            for p in br:
                dst_.extend(['_', str(p.seq_number)])
            dst_.append('.tif')
            dst_filename = ''.join(dst_)
            dst_path = os.path.join(dst, dst_filename)

            # Если уже сведено и размер файла больше 1МБ, выходим
            if os.path.exists(dst_path) and os.stat(dst_path).st_size > 1024*1024*1:
                return

            cmd = base_cmd[:]
            cmd.append(dst_path)
            cmd.extend([p.tif for p in br])

            p = Process(cmd, cwd=dst)
            p.run()

            result = ' '.join([p.result, p.errors]).lower()
            if 'error' not in result:
                results['blended'].append(br)
            else:
                results['errors'].append(result)

            message = 'Файлы {0} сведены в {1}'.format(
                ', '.join([p.tif for p in br]),
                dst_path,
            )
            log.debug(message)

            e = br[0].exif
            for key in _exif_clear:
                try:
                    del e[key]
                except KeyError:
                    pass

            e.save_file(dst_path)
            log.debug('Метаданные файла `{0}` обновлены'.format(dst_path))

            log.progress()

    threads = [threading.Thread(target=worker) for _i in range(cpus)]

    for thread in threads:
        thread.setDaemon(True)
        thread.start()

    for thread in threads:
        thread.join()

    if not results['errors']:
        blend_file = os.path.join(dst, '.blend')
        with open(blend_file, 'w') as f:
            f.write('ok')
        log.status = 'Сведение завершено'
    else:
        log.status = 'Сведение завершено с ошибками'
        log.debug(repr(results['errors']))

    return results


def blend_dir(src, dst, force):
    tiff_files = []
    for entry in scandir.scandir(src):
        if entry.isdir():
            continue
        filename, _n, ext = entry.name.lower().rpartition('.')
        if ext == 'tif':
            tiff_files.append(TifPhoto(tif=os.path.join(src, entry.name)))

    if tiff_files:
        if force:
            shutil.rmtree(dst, ignore_errors=True)

        makedirs(dst, mode=0o775)
        if not os.path.exists(os.path.join(dst, '.blend')):
            blend_tif(tiff_files, dst)
