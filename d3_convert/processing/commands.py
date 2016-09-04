#coding: utf-8
from __future__ import unicode_literals, absolute_import

import os


def copy_exif_to_cmd(src_photo, dst_photo, excludes=None):
    cmd = [
        'exiftool',
        '-tagsFromFile',
        src_photo.filename,
        '-overwrite_original',
    ]

    if excludes and isinstance(excludes, (list, tuple)):
        cmd.extend(['-{0}='.format(tag) for tag in excludes])

    cmd.append(dst_photo.filename)
    return cmd


def get_blend_filename(dstpath, batch):
    fn = list()
    for photo in batch:
        fn.append(str(photo.seq_number))

    return os.path.join(dstpath, 'IMG_{0}.tif'.format('_'.join(fn)))


def blend_to_cmd(dst_filename, batch):

    cmd = [
        'enfuse',
        '--compression=deflate',
        '-o',
        dst_filename,
    ]

    cmd.extend([p.filename for p in batch])

    return cmd


def convert_jpg_to_cmd(src_filename, dst_filename, **kwargs):
    return [
        'convert',
        src_filename,
        '-rotate',  '90',
        dst_filename,
    ]


def convert_to_cmd(dstdir, img_format, filename, wb=None, force=False):
    cmd = [
        'ufraw-batch',
        '--out-type={0}'.format(img_format),
        '--out-depth=8',
        '--create-id=no',
        '--zip',
        '--exif',
        #'--silent',
        '--out-path={0}'.format(dstdir),
        filename,
    ]

    if wb and isinstance(wb, (list, tuple)):
        cmd.extend(list(wb))

    if force:
        cmd.append('--overwrite')

    return cmd


def get_wb_cmd(src_file, dst_file):
    return [
        'ufraw-batch',
        '--create-id=only',
        '--out-type=tif',
        '--out-depth=16',
        '--wb=auto',
        '--silent',
        '--overwrite',
        '--output={0}'.format(dst_file),
        src_file,
    ]
