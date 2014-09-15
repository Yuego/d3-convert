#coding: utf-8


class MakerBase(object):

    def __init__(self, photo, exif):
        self.photo = photo
        self.exif = exif

    def is_bracketed(self):
        raise NotImplementedError()

    def __calculate_exposure(self, value):
        if '/' in value:
            up, dn = value.split('/')
            return 1.0/int(dn)
        else:
            return float(value)

    def exposure(self):
        return self.__calculate_exposure(self.exif['Exif.Photo.ExposureTime'])

    def bracket_value(self):
        raise NotImplementedError()

    def bracket_count(self):
        #TODO: определять количество кадров
        return 3
