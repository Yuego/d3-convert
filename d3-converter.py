#!/usr/bin/env python3
#coding: utf-8
"""Converter

Usage:
    convert <src> [--dst=<dstdir>] [--force] [--verbose]
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
from d3_convert import db
from d3_convert.log import log
from d3_convert.db import FileList
from d3_convert.version import __version__
from docopt import docopt
import os

#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
#Session = sessionmaker()
#session = Session()


if __name__ == '__main__':
    arguments = docopt(__doc__, version='D3 Converter v' + __version__)

    src = arguments.pop('<src>', None)
    if src is not None:
        #from d3_convert.config import dsn
        src = os.path.realpath(src)

        dst = arguments.pop('--dst', None)
        if dst is None:
            dst = src

        force = arguments.pop('--force', False)
        log.enabled = arguments.pop('--verbose', False)

        #engine = create_engine(dsn.format(path=src), echo=False)
        #Session.configure(bind=engine)
        #session = Session()
        #db.Base.metadata.create_all(engine)

        convert_all(src, dst, force)
