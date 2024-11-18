#!/usr/bin/env python3

from setuptools import setup

setup(
    name = 'longplayer',
    version = '0.1.3',
    description = 'Longplayer, a thousand-year long musical composition, implemented in Python',
    long_description = open("README.md", "r").read(),
    long_description_content_type = "text/markdown",
    author = 'Daniel Jones and Jem Finer',
    author_email = 'dan-code@erase.net',
    url = 'https://github.com/TheLongplayerTrust/longplayer-python',
    packages = ['longplayer'],
    install_requires = [
        'soundfile',
        'sounddevice',
        'numpy',
    ],
    keywords = ['sound', 'music', 'time', 'soundart'],
    classifiers = [
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Artistic Software',
        'Topic :: Communications',
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop'
    ],
    package_data={
        'longplayer': ['audio/20-20.aif']
    },
    include_package_data=True,
    entry_points={
        'longplayer': [
            'longplayer=longplayer:__main__',
        ],
    },
)
