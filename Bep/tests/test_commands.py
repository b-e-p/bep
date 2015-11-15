#!/usr/bin/python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 09-20-2013
# Purpose: to make sure that everything works as expected.
#----------------------------------------------------------------

import subprocess


def test_install():
    ret_code = subprocess.call("bep install github pypa/pip", shell=True)
    assert ret_code == 0

def test_update():
    ret_code = subprocess.call("bep update github pip --branch=master", shell=True)
    assert ret_code == 0

def test_turn_off():
    ret_code = subprocess.call("bep turn_off github pip --branch=master", shell=True)
    assert ret_code == 0

def test_turn_on():
    ret_code = subprocess.call("bep turn_on github pip --branch=master", shell=True)
    assert ret_code == 0

def test_remove():
    ret_code = subprocess.call("bep remove github pip --branch=master", shell=True)
    assert ret_code == 0


