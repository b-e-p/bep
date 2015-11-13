#! /usr/bin/env python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 08-30-2013
# Purpose: this is the entry point when called
        # and built w/ setuptools.
# License: BSD
#----------------------------------------------------------------

from Bep import _run_bep     # defined in the Bep package's __init__.py

#_run_bep()  # for using distutils

# for using setuptools # (also, this script needs to have a .py extension).
def main():
    _run_bep()

