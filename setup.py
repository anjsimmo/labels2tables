#!/usr/bin/env python

from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

setup(
    name='labels2tables',
    version='0.1.0',
    description="Turns bibtex keywords into an academic summary table",
    long_description=readme,
    author='Andrew Simmons',
    author_email='anjsimmo@gmail.com',
    url='https://github.com/anjsimmo/labels2tables',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing :: Markup',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    packages=['labels2tables'],
    install_requires=[
        'bibtexparser',
        'enum34'
    ],
    test_suite="tests"
)
