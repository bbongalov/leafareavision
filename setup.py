#!/usr/bin/env python3
import sys

from distutils.core import setup

name = "leafcalc"

# Python 2.4 or later needed
if sys.version_info < (3, 7, 0, 'final', 0):
    raise RuntimeError(f'Python 3.7 or later is required, you have {sys.version_info}')


setup(
    name=name,
    version='0.9.0',
    description='Estimate the area of scanned images.',
    include_package_data=True,
    url='https://github.com/bbongalov',
    author='Boris Bonaglov',
    author_email='boris@bongalov.com',
    license='MIT License',
    keywords='leaf area ecology plant science automation image analysis',
    packages=['python-leafcalc'],
    scripts=['./bin/LeafCalc.py'],
    install_requires=[
        "numpy",
        "pandas",
        "opencv-python",
        "exif",
        "scikit-image"]
    )
