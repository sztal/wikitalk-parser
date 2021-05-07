#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://wikitalk_parser.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='wikitalk_parser',
    version='0.0.1',
    description='Wikipedia talk threads parser aware of outdent formatting.',
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Szymon Talaga',
    author_email='stalaga@protonmail.com',
    url='https://github.com/sztal/wikitalk-parser',
    packages=[
        *find_packages()
        #'wikitalk_parser',
    ],
    setup_requires=[
        'pytest-runner',
        'pylint'
    ],
    tests_require=[
        'pytest',
        'pytest-pylint',
        'coverage'
    ],
    test_suite='tests',
    package_dir={'wikitalk_parser': 'wikitalk_parser'},
    include_package_data=True,
    install_requires=[
        'python-dateutil>=2.8'
    ],
    license='MIT',
    zip_safe=False,
    keywords='wikitalk_parser',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English'
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
)
