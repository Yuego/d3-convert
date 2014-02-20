#!/usr/bin/env python3
#coding: utf-8
"""Converter

Usage:
    convert <src> [--dst=<dstdir>] [--force] [--autowb|--nowb] [--verbose]
    convert (-h | --help)
    convert --version

Options:
    -h --help       Show this screen.
    --version       Show version
    --dst=<dstdir>  Set destination dir.
    --force         Force reconvert existing files

"""
from __future__ import unicode_literals, absolute_import

from d3_convert.convert import convert_all
from d3_convert.log import log
from d3_convert.version import __version__
from docopt import docopt
import os


if __name__ == '__main__':
    arguments = docopt(__doc__, version='D3 Converter v' + __version__)

    src = arguments.pop('<src>', None)
    if src is not None:
        src = os.path.realpath(src)

        dst = arguments.pop('--dst', None)
        if dst is None:
            dst = src

        autowb = arguments.pop('--autowb', False)
        nowb = arguments.pop('--nowb', False)
        force = arguments.pop('--force', False)
        log.enabled = arguments.pop('--verbose', False)

        convert_all(src=src, dst=dst, force=force, autowb=autowb, nowb=nowb)
