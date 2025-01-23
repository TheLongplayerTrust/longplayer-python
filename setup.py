#!/usr/bin/env python3

import os
from setuptools import setup

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "longplayer", "__init__.py")
    with open(version_file, "r") as f:
        for line in f:
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")

setup(
    name = 'longplayer',
    version = get_version(),
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
        'samplerate',
        'numpy',
        'blockbuffer',
        'requests',
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
        'longplayer': ['audio/20-20.wav']
    },
    include_package_data=True,
    entry_points={
        'longplayer': [
            'longplayer=longplayer:__main__',
        ],
    },
)
