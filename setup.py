#!/usr/bin/env python

from distutils.core import setup, Command
import setuptools

import sys

if (float(sys.version[:3]) < 2.5):
    print('Require python 2.5 or later')
    sys.exit(-1)

setup(name='Legume',
      version='0.4',
      description='Reliable UDP library',
      author='Dale Reidy',
      url='http://code.google.com/p/legume/',
      packages=setuptools.find_packages('.'),
      license='BSD',
      package_dir = {'':'.'},
      classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet',
        ]
     )
