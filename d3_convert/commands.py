#coding: utf-8
from __future__ import unicode_literals, absolute_import


def convert_to_cmd(dstdir, img_format, filename, wb=None):
    cmd = [
        'ufraw-batch',
        '--out-type={0}'.format(img_format),
        '--out-depth=8',
        '--create-id=no',
        '--zip',
        #'--silent',
        #'--overwrite',
        '--out-path={0}'.format(dstdir),
        filename,
    ]

    if wb and isinstance(wb, (list, tuple)):
        cmd.extend(list(wb))

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
