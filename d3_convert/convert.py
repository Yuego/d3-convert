#coding: utf-8

from d3_convert.blend import blend_tif
from d3_convert.lock import is_locked
from d3_convert.log import log
from d3_convert.photo import CR2Photo
from d3_convert.process import Process
from d3_convert.utils import cpus, makedirs

import glob
import io
from lxml import etree
import os
import scandir
import shutil
from time import time
import threading
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

convert_filename = '.convert'
skip_names = [
    '_tif',
    'blend',
]


class IncompleteDirError(Exception):
    pass

def get_wb(photos, auto, nowb):
    photo = photos[0]

    if auto:
        output = os.path.join(photo.raw_dir, 'img')
        cmd = [
            'ufraw-batch',
            '--create-id=only',
            '--out-type=tif',
            '--out-depth=16',
            '--wb=auto',
            '--silent',
            '--overwrite',
            '--output={0}'.format(output),
            photo.raw,
        ]

        proc = Process(cmd, cwd=photo.raw_dir)
        proc.run()
        proc.wait()

    wb = ['--wb=camera']
    if not nowb:
        settings_list = glob.glob(os.path.join(photo.raw_dir, '*.ufraw'))
        if settings_list:
            settings = settings_list[0]

            doc = etree.parse(settings)
            temp = doc.find('Temperature')
            green = doc.find('Green')

            if temp is not None and green is not None:
                wb = [
                    '--temperature={0}'.format(temp.text),
                    '--green={0}'.format(green.text)
                ]
            if auto:
                os.unlink(settings)

    return wb


def convert_cr2(photos, dst, force=False, autowb=False, nowb=False):
    if force:
        shutil.rmtree(dst, ignore_errors=True)

    makedirs(dst, mode=0o775)

    source_file = os.path.join(dst, '.source')
    with io.open(source_file, 'w') as f:
        f.write(photos[0].raw_dir)

    base_cmd = [
        'ufraw-batch',
        '--create-id=only',
        '--out-type=tif',
        '--out-depth=8',
        '--create-id=no',
        '--zip',
        #'--wb=camera',
        #'--silent',
        #'--overwrite',
        '--out-path={0}'.format(dst)
    ]
    base_cmd.extend(get_wb(photos, autowb, nowb))

    q = Queue()
    for p in photos:
        q.put(p)
    #total_photos = len(photos)

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
            p = Process(cmd, cwd=dst)
            p.run()

            result = ' '.join([p.result, p.errors]).lower()
            if 'saved' in result:
                log.debug('`{0}` сконвертирован в `{1}`'.format(photo.raw, photo.tif))
            log.progress()

    threads = [threading.Thread(target=worker) for _i in range(cpus)]

    for thread in threads:
        thread.setDaemon(True)
        thread.start()

    for thread in threads:
        thread.join()

    if not results['errors']:
        convert_file = os.path.join(dst, convert_filename)
        with open(convert_file, 'w') as f:
            f.write('ok')
        log.status = 'Каталог `{0}` сконвертирован'.format(photos[0].raw_dir)
    else:
        log.status = 'Каталог `{0}` сконвертирован с ошибками'.format(photos[0].raw_dir)
        log.warning(repr(results))

    return results


def collect_cr2(files, srcpath, dstpath):
    cr2_files = []
    for file in files:
        filename, nothing, ext = file.lower().rpartition('.')
        if ext == 'cr2':
            srcfile = os.path.join(srcpath, file)
            photo = CR2Photo(srcfile)
            # Проверяем, читается ли exif файла
            try:
                _z = photo.exif
            except Exception:
                raise IncompleteDirError()

            photo.tif_dir = dstpath
            cr2_files.append(photo)
    return cr2_files


def convert_all(src, dst, force, autowb=False, nowb=False):
    for (srcpath, dirs, files) in scandir.walk(src):

        # Пропускаем специальные каталоги
        name = os.path.basename(srcpath)
        if name in skip_names:
            log.debug('Пропуск служебных каталогов `{0}`'.format(srcpath))
            continue

        rel_path = srcpath.replace(src, '').strip('/')
        dstpath = os.path.join(dst, rel_path, '_tif')

        if not force:
            convert_file = os.path.join(dstpath, convert_filename)
            dir_mtime = os.stat(srcpath).st_mtime

            # Пропускаем помеченные каталоги
            if os.path.exists(convert_file):
                log.debug('Пропуск сконвертированного каталога `{0}`'.format(srcpath))
                continue
            # Пропускаем каталоги, созданные или изменённые недавно
            elif (int(time()) - dir_mtime) < 60 * 5:
                log.debug('Пропуск недавно изменённого каталога `{0}`'.format(srcpath))
                continue
            # Пропускаем каталоги, пролежавшие больше 2 недель
            elif (int(time()) - dir_mtime) > 60 * 60 * 24 * 14:
                log.debug('Пропуск "старого" каталога: `{0}`'.format(srcpath))
                continue
            elif is_locked(src, srcpath, 'torrent'):
                log.warning('Пропуск занятого торрентом каталога: `{0}`'.format(srcpath))
                log.warning('Дождитесь завершения загрузки, либо удалите торрент из торрент-клиента.')
                continue

        if is_locked(src, srcpath, 'ufraw-batch') or is_locked(src, srcpath, 'enfuse'):
            log.status = 'Каталог `{0}` уже обрабатывается другой копией конвертера. Пропускаем'.format(srcpath)
            continue

        try:
            cr2_files = collect_cr2(files=files, srcpath=srcpath, dstpath=dstpath)
        except IncompleteDirError:
            log.warning('Не все файлы в каталоге `{0}` целостны. Пропускаем.'.format(srcpath))
            continue

        if cr2_files:
            log.status = 'Обработка каталога: `{0}`'.format(srcpath)

            convert_cr2(photos=cr2_files, dst=dstpath, force=force, autowb=autowb, nowb=nowb)
            blend_dir = os.path.join(dstpath, 'blend')
            blend_tif(photos=cr2_files, dst=blend_dir)
        else:
            log.debug('Пропуск "пустого" каталога `{0}`'.format(srcpath))
