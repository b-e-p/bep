#!/usr/bin/python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 09-20-2013
# Purpose: make sure everything works as expected.
#----------------------------------------------------------------

# import os
# import tempfile
import subprocess


repo1, r1 = 'b-e-p/testrepo1', 'testrepo1'
repo2, r2 = 'b-e-p/testrepo2', 'testrepo2'



def test_install():
    ret_code = subprocess.call("bep install github {}".format(repo1), shell=True)
    assert ret_code == 0


def test_turn_off():
    ret_code = subprocess.call("bep turn_off github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_turn_on():
    ret_code = subprocess.call("bep turn_on github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_update():
    ret_code = subprocess.call("bep update github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_install_another_repo():
    ret_code = subprocess.call("bep install github {}".format(repo2), shell=True)
    assert ret_code == 0


def test_update_all():
    ret_code = subprocess.call("bep update --all", shell=True)
    assert ret_code == 0


def test_list():
    ret_code = subprocess.call("bep list", shell=True)
    assert ret_code == 0


def test_remove():
    ret_code = subprocess.call("bep remove github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_remove_r2():
    ret_code = subprocess.call("bep remove github {} --branch=master".format(r2), shell=True)
    assert ret_code == 0

