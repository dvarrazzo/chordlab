#!/usr/bin/env python
"""
chordlab -- setup script
"""

from setuptools import setup, find_packages

version = "0.1"

setup(
    name = 'chordlab',
    description = 'A tool to render songsheets',
    author = 'Daniele Varrazzo',
    author_email = 'daniele.varrazzo@gmail.com',
    url = 'https://github.com/dvarrazzo/chordlab/',
    license = 'BSD',
    packages = find_packages(),
    package_data = {'chordlib': ['data/*']},
    entry_points = {'console_scripts': [
        'chordlab = chordlib.script:script', ]},
    classifiers = [],
    zip_safe = False,
    version = version,
    use_2to3 = True,
)

