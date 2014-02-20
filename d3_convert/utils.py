#coding: utf-8
from __future__ import unicode_literals, absolute_import

import multiprocessing
import os

cpus = multiprocessing.cpu_count()


def makedirs(path, mode=0o777):
    if not path or os.path.exists(path):
        return
    (head, tail) = os.path.split(path)
    makedirs(head, mode)
    os.mkdir(path)
    os.chmod(path, mode)
