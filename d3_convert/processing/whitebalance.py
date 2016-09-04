# coding: utf-8
from __future__ import unicode_literals, absolute_import

from lxml import etree
import os
import glob

from .commands import get_wb_cmd
from .process import Process


class WhiteBalance(object):

    def __init__(self):
        self.mode = 'camera'
        self.filename = None

    def gen_camera_wb(self, **kwargs):
        return ['--wb=camera']

    def gen_manual_wb(self, photo=None, source=None, **kwargs):
        temp = None
        green = None

        if photo is not None:
            source = photo.dirname

        if os.path.isfile(source):
            config_files = [source]
        elif os.path.isdir(source):
            config_files = glob.glob(os.path.join(source, '*.ufraw'))
        else:
            raise ValueError('Unknown UFRAW config source: {0}'.format(source))

        for config_path in config_files:
            doc = etree.parse(config_path)
            temp = doc.find('Temperature')
            green = doc.find('Green')

            if temp is not None and green is not None:
                break
        if temp is None or green is None:
            raise ValueError('WhiteBalance settings file not found in `{0}`'.format(source))

        return [
            '--temperature={0}'.format(temp.text),
            '--green={0}'.format(green.text)
        ]

    def gen_auto_wb(self, photo, **kwargs):
        output = os.path.join(photo.dirname, 'wb')
        cmd = get_wb_cmd(src_file=photo.filename, dst_file=output)

        proc = Process(cmd, cwd=photo.dirname)
        proc.run()
        proc.wait()

        config_path = os.path.join(photo.dirname, 'wb.ufraw')
        result = self.gen_manual_wb(source=config_path)

        os.unlink(config_path)

        return result

    def setup(self, mode, filename=None):
        if mode is None:
            mode = 'camera'

        assert mode in ['auto', 'camera', 'manual'], 'Unknown WhiteBalance mode: {0}'.format(mode)

        self.mode = mode
        #self.filename = filename

    def generate_for(self, photo):
        return getattr(self, 'gen_{0}_wb'.format(self.mode))(photo=photo)
