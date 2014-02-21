#coding: utf-8
from __future__ import unicode_literals, absolute_import

import os
import psutil


def get_pids_by_name(name):
    for p in psutil.process_iter():
        if name in p.name:
            yield p


def dir_locked_by_process(dir, process):
    for f in process.get_open_files():
        if f.path.startswith(dir):
            return True

    return False


def is_locked(dir, process_name):
    dir = os.path.realpath(dir)

    for process in get_pids_by_name(process_name):
        if dir_locked_by_process(dir, process):
            return True

    return False
