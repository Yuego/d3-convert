#coding: utf-8
from __future__ import unicode_literals, absolute_import


def convert_to_tiff_cmd(dstdir):
    return [
        'ufraw-batch',
        '--create-id=only',
        '--out-type=tif',
        '--out-depth=8',
        '--create-id=no',
        '--zip',
        #'--silent',
        #'--overwrite',
        '--out-path={0}'.format(dstdir)
    ]


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
