#coding: utf-8
from __future__ import unicode_literals, absolute_import

from d3_convert.blend import blend_tif
from d3_convert.log import log
from d3_convert.photo import CR2Photo
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


def convert_cr2(photos, dst):
    base_cmd = [
        'ufraw-batch',
        '--create-id=only',
        '--out-type=tif',
        '--out-depth=8',
        '--create-id=no',
        '--zip',
        '--wb=camera',
        #'--silent',
        #'--overwrite',
        '--out-path={0}'.format(dst)
    ]

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

            log.trace('processing file', photo.raw)
            cmd = base_cmd[:]
            cmd.append(photo.raw)
            p = Process(cmd, cwd=dst)
            p.run()

            result = ' '.join([p.result, p.errors]).lower()
            if 'saved' in result:
                photo.tif_dir = dst
                log.trace('saved to', photo.tif)

    threads = [threading.Thread(target=worker) for _i in range(cpus)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    if not results['errors']:
        convert_file = os.path.join(dst, '.convert')
        with open(convert_file, 'w') as f:
            f.write('ok')

    return results


def convert_all(src, dst, force):
    write_source_path = bool(dst != src)

    for (srcpath, dirs, files) in scandir.walk(src):
        rel_path = srcpath.replace(src, '').strip('/')
        dstpath = os.path.join(dst, rel_path, '_tif')

        cr2_files = []
        for file in files:
            filename, nothing, ext = file.lower().rpartition('.')
            if ext == 'cr2':
                srcfile = os.path.join(srcpath, file)
                photo = CR2Photo(srcfile)
                photo.tif_dir = dstpath
                cr2_files.append(photo)

        if cr2_files:
            log.trace('processing directory: ', srcpath)

            if force:
                shutil.rmtree(dstpath, ignore_errors=True)

            makedirs(dstpath, mode=0o775)

            if write_source_path:
                pathfile = os.path.join(dst, rel_path, '.source')
                with open(pathfile, 'w') as f:
                    f.write(srcpath)

            convert_cr2(cr2_files, dstpath)


            blend_dst = os.path.join(dstpath, 'blend')
            if force:
                shutil.rmtree(blend_dst, ignore_errors=True)

            makedirs(blend_dst, mode=0o775)
            blend_tif(cr2_files, blend_dst)
