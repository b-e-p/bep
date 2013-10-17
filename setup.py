#!/usr/bin/python

"""
#----------------------------------------------------------------
Author: Jason Gors <jasonDOTgorsATgmail>
Creation Date: 09-20-2013
Purpose: how to set-up & install.
License: BSD
#----------------------------------------------------------------
"""

import os

# bring in the info from core.release_info
from Bep.core.release_info import (
        name,
        __version__, 
        description,
        author,
        email,
        url,
)


setup_args = dict(
    name=name,
    version=__version__, 
    description=description,
    #long_description=open('README.md').read(),
    #long_description='For installation and use info see {}'.format(url),
    author=author,
    author_email=email,
    url=url,
    license=license,
    packages=['Bep', 'Bep.core', 'Bep.languages', 'Bep.scripts', 'Bep.tests'],
)

# this should be done by setup(), but just in case (so we don't overwrite someone's packages file):
usr_home_dir = os.path.expanduser('~')  # specifies the user's home dir  
bep_pkgs_fname = '.bep_packages'
if not os.path.exists( os.path.join(usr_home_dir, bep_pkgs_fname) ):
    #setup_args['data_files'] = [('Bep/data/', ['Bep/data/{}'.format(bep_pkgs_fname)])]
    setup_args['data_files'] = [(usr_home_dir, ['Bep/data/{}'.format(bep_pkgs_fname)])]

### use setuptools if it's installed, if not, then use distutils
try:
    ### for using setuptools (maybe needed for windows instead of distutils?)
    import setuptools
    setuptools._dont_write_bytecode = True
    from setuptools import setup
    setup_args['entry_points'] = {
                'console_scripts': ['bep = Bep.scripts.bep_script:main']
                }
except ImportError:
    ### for using distutils
    from distutils.core import setup
    setup_args['scripts'] = ['Bep/scripts/bep']


def main():
    setup(**setup_args)

if __name__ == '__main__':
    main()
