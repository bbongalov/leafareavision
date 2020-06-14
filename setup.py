from setuptools import setup
import sys

setup(
    name='area',
    version='0.1.2',
    author='Boris Bongalov',
    author_email='boris@bongalov.com',
    packages=['leafareavision'],
    entry_points={
        'console_scripts': [
            'area=LAV_assess:main',
            'area=LAV_pp:main'],
    }
    url='https://github.com/bbongalov/leafareavision',
    license='LICENSE',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
    ],
    description='Quick and accurate estimation of the area of scanned leaves.',
    install_requires=[
        "numpy",
        "pandas",
	    "opencv-python",
	    "exif",
	    "scikit-image",
        "glob",
        "multiprocessing",
        "argparse",
        "PIL"
    ],
    python_requires='>=3.5',
    package_data ={
        'area': ['data/BEL-T20-B1S-L3.jpg']
    }
)
