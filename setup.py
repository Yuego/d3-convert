#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

from d3_convert.version import __version__

for cmd in ('egg_info', 'develop', 'build_sphinx', 'upload_sphinx'):
    if cmd in sys.argv:
        from setuptools import setup

setup(
    name='d3_convert',
    version=__version__,
    author='Artem Vlasov',
    author_email='root@proscript.ru',
    url='',
    #download_url='https://github.com/Yuego/krpano/archive/%s.tar.gz' % __version__,

    description='D3 Converter',
    long_description=open('README.rst').read(),

    license='',
    install_requires=[
        'scandir',
        'gi',  # gexiv2
    ],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Russian',
        'Programming Language :: Python',
        #'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
