#!/usr/bin/env python
from setuptools import setup, find_packages

import sys

from d3_convert.version import __version__

extra_requires = []

PY3 = sys.version_info[0] == 3
PY35_plus = PY3 and sys.version_info[1] >= 5

if not PY35_plus:
    extra_requires.append('scandir')

setup(
    name='d3_convert',
    version=__version__,
    author='Artem Vlasov',
    author_email='root@proscript.ru',
    url='https://github.com/Yuego/d3-convert',

    description='D3 Converter',
    long_description=open('README.rst').read(),

    license='MIT',
    install_requires=[
        'docopt',
        'exiftool',
        #'PyGObject',
        # media-libs/gexiv2
        'lxml',
        'psutil>=2',
    ] + extra_requires,
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 2 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Russian',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
