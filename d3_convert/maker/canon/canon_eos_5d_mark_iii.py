#coding: utf-8

from d3_convert.maker.canon import Maker as MakerBase
from d3_convert.process import Process


class Maker(MakerBase):

    def bracket_count(self):
        cmd = [
           'exiftool',
           '-n',
           '-S',
           '-t',
           '-MakerNotes:AEBShotCount',
           self.photo.raw
        ]
        p = Process(cmd, cwd=self.photo.raw_dir)
        p.run()

        if p.success:
            return int(p.result.split(' ')[0])
        else:
            raise Exception(p.errors)
            return 3
