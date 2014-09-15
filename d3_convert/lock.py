#coding: utf-8

import os
import psutil

psutil_ver = int(psutil.__version__.split('.')[0])

if psutil_ver < 2:
    get_open_files = lambda x: x.get_open_files()
else:
    get_open_files = lambda x: x.open_files()


def dir_locked_by_process(dir, process):
    try:
        for f in get_open_files(process):
            if f.path.startswith(dir):
                return True
    except psutil.AccessDenied:
        pass
    return False


def get_pids_by_name(name):
    for p in psutil.process_iter():
        if name in p.name:
            yield p


def is_locked(root_dir, src_dir, process_name):
    if root_dir == src_dir:
        return False

    src_dir = os.path.realpath(src_dir)

    for process in get_pids_by_name(process_name):
        if dir_locked_by_process(src_dir, process):
            return True

    src_dir = os.sep.join(src_dir.split(os.sep)[:-1])
    if root_dir != src_dir:
        return is_locked(root_dir=root_dir, src_dir=src_dir, process_name=process_name)

    return False
