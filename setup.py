#!/usr/bin/env python3

from setuptools import setup

setup(
    name = 'longplayer',
    version = '0.0.1',
    description = 'Longplayer, a thousand-year long musical composition, implemented in Python',
    long_description = open("README.md", "r").read(),
    long_description_content_type = "text/markdown",
    author = 'Daniel Jones',
    author_email = 'dan-code@erase.net',
    url = 'https://github.com/TheLongplayerTrust/longplayer-python',
    packages = ['longplayer'],
    install_requires = ['soundfile', 'sounddevice', 'samplerate'],
    keywords = ('sound', 'music'),
    classifiers = [
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Artistic Software',
        'Topic :: Communications',
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop'
    ]
)
