#!/usr/bin/env python3
#coding: utf-8
"""D3 Blender

Usage:
    blend <src> [--dst=<dstdir>] [--force] [--verbose]
    blend (-h | --help)
    blend --version

Options:
    -h --help       Show this screen.
    --version       Show version
    --dst=<dstdir>  Set destination dir.
    --force         Force reblend existing files

"""
from __future__ import unicode_literals, absolute_import

from d3_convert.blend import blend_dir
from d3_convert.log import log

from d3_convert.version import __version__
from docopt import docopt
import os


if __name__ == '__main__':
    arguments = docopt(__doc__, version='D3 Blender v' + __version__)

    src = arguments.pop('<src>', None)
    if src is not None:
        src = os.path.realpath(src)

        dst = arguments.pop('--dst', None)
        if dst is None or dst == src:
            dst = os.path.join(src, 'blend')

        force = arguments.pop('--force', False)

        verbose = arguments.pop('--verbose', False)
        if verbose:
            log.level = log.DEBUG

        blend_dir(src, dst, force)
