#!/usr/bin/python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 09-20-2013
# Purpose: make sure everything works as expected.
#----------------------------------------------------------------

import os
import tempfile
import subprocess
import shutil


repo1, r1 = 'b-e-p/testrepo1', 'testrepo1'
repo2, r2 = 'b-e-p/testrepo2', 'testrepo2'

# make something like this into decorator so that local funcs can be wrapped with a temp dir to use and then
# removed once finished
# def make_test_repo():
    # with open(os.path.join(tdir, 'test_file.txt'), 'w') as f:
        # f.write('some text')
    # cwd = os.getcwd()
    # os.chdir(tdir)
    # ret_code = subprocess.call("git init; git add .; git commit -m 'add test_file to repo'", shell=True)
    # assert ret_code == 0
    # os.chdir(cwd)
    # os.rmdir(tdir)


def test_local_git_repo():
    try:
        tdir = tempfile.mkdtemp()
        local_repo_name = 'testrepo_local'
        local_repo_dir = os.path.join(tdir, local_repo_name)

        cmd = "git clone https://github.com/b-e-p/testrepo1 {}".format(local_repo_dir)
        ret_code = subprocess.call(cmd, shell=True)
        assert ret_code == 0

        ret_code = subprocess.call("bep install local {}".format(local_repo_dir), shell=True)
        assert ret_code == 0

        ret_code = subprocess.call("bep turn_off local {} --branch=master".format(local_repo_name), shell=True)
        assert ret_code == 0

        ret_code = subprocess.call("bep turn_on local {} --branch=master".format(local_repo_name), shell=True)
        assert ret_code == 0

        ret_code = subprocess.call("bep update local {} --branch=master".format(local_repo_name), shell=True)
        assert ret_code == 0

        ret_code = subprocess.call("bep remove local {} --branch=master".format(local_repo_name), shell=True)
        assert ret_code == 0
    finally:
        shutil.rmtree(tdir)



def test_install_repo1():
    ret_code = subprocess.call("bep install github {}".format(repo1), shell=True)
    assert ret_code == 0


def test_turn_off_r1():
    ret_code = subprocess.call("bep turn_off github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_turn_on_r1():
    ret_code = subprocess.call("bep turn_on github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_update_r1():
    ret_code = subprocess.call("bep update github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_install_repo2():
    ret_code = subprocess.call("bep install github {}".format(repo2), shell=True)
    assert ret_code == 0


def test_update_all():
    ret_code = subprocess.call("bep update --all", shell=True)
    assert ret_code == 0


def test_list():
    ret_code = subprocess.call("bep list", shell=True)
    assert ret_code == 0


def test_remove_r1():
    ret_code = subprocess.call("bep remove github {} --branch=master".format(r1), shell=True)
    assert ret_code == 0


def test_remove_r2():
    ret_code = subprocess.call("bep remove github {} --branch=master".format(r2), shell=True)
    assert ret_code == 0
