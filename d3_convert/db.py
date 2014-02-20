#coding: utf-8
from __future__ import unicode_literals, absolute_import

from sqlalchemy import Integer, BigInteger, SmallInteger, String, Date, Boolean
from sqlalchemy import Sequence, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import deferred, relationship
from datetime import date
Base = declarative_base()


class FileList(Base):
    __tablename__ = 'filelist'
    id = Column(Integer, primary_key=True)
    path = Column(String(255), index=True)
    file_date = Column(Date)
    convert_date = Column(Date)
