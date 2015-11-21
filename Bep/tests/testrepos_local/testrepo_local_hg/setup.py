#!/usr/bin/python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 11-01-2015
# Purpose: use to set-up & install a temp repo for unit-testing
# License: BSD
#----------------------------------------------------------------


setup_args = dict(
    name='testrepo_local_hg',
    version='1.0',
    description='test repo for unit-testing',
    author="jason gors",
    packages=['Testrepo_local_hg']
)


### use setuptools if it's installed, if not, then use distutils
try:
    ### for using setuptools (maybe needed for windows instead of distutils?)
    import setuptools
    setuptools._dont_write_bytecode = True
    from setuptools import setup
except ImportError:
    ### for using distutils
    from distutils.core import setup


def main():
    setup(**setup_args)

if __name__ == '__main__':
    main()
