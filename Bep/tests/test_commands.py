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

from nose.tools import ok_


github_repo1 = 'b-e-p/testrepo1'
github_repo2 = 'b-e-p/testrepo2'
bitbucket_repo_git = 'jgors/testrepo_git'
bitbucket_repo_hg = 'jgors/testrepo_hg'
repo_name = lambda r: r.split('/')[-1]


def check_local_repo(cmd, local_repo_name, branch):
    try:
        tdir = tempfile.mkdtemp()
        local_repo_dir = os.path.join(tdir, local_repo_name)

        # cmd = "git clone https://github.com/b-e-p/testrepo1 {}".format(local_repo_dir)
        sp_cmd = "{} {}".format(cmd, local_repo_dir)
        ret_code = subprocess.call(sp_cmd, shell=True)
        ok_(ret_code == 0)

        ret_code = subprocess.call("bep install local {}".format(local_repo_dir), shell=True)
        ok_(ret_code == 0)

        ret_code = subprocess.call("bep turn_off local {} --branch={}".format(local_repo_name, branch), shell=True)
        ok_(ret_code == 0)

        ret_code = subprocess.call("bep turn_on local {} --branch={}".format(local_repo_name, branch), shell=True)
        ok_(ret_code == 0)

        ret_code = subprocess.call("bep update local {} --branch={}".format(local_repo_name, branch), shell=True)
        ok_(ret_code == 0)

        ret_code = subprocess.call("bep remove local {} --branch={}".format(local_repo_name, branch), shell=True)
        ok_(ret_code == 0)
    finally:
        shutil.rmtree(tdir)


def test_local_repo():
    yield check_local_repo, 'git clone https://github.com/{}'.format(github_repo1), 'github_testrepo_local1', 'master'
    yield check_local_repo, 'git clone https://github.com/{}'.format(github_repo2), 'github_testrepo_local2', 'master'
    yield check_local_repo, 'git clone https://bitbucket.org/{}'.format(bitbucket_repo_git), 'bitbucket_testrepo_git_local', 'master'
    yield check_local_repo, 'hg clone https://bitbucket.org/{}'.format(bitbucket_repo_hg), 'bitbucket_testrepo_hg_local', 'default'


def check_install_github_repo(github_repo):
    ret_code = subprocess.call("bep install github {}".format(github_repo), shell=True)
    ok_(ret_code == 0)

def test_install_github_repo():
    yield check_install_github_repo, github_repo1
    yield check_install_github_repo, github_repo2


def check_install_bitbucket_repo(bitbucket_repo, repo_type):
    ret_code = subprocess.call("bep install bitbucket {} {}".format(bitbucket_repo, repo_type), shell=True)
    ok_(ret_code == 0)

def test_install_bitbucket_hg_repo():
    yield check_install_bitbucket_repo, bitbucket_repo_git, 'git'
    yield check_install_bitbucket_repo, bitbucket_repo_hg, 'hg'


def test_turn_off_github_repo1():
    ret_code = subprocess.call("bep turn_off github {} --branch=master".format(repo_name(github_repo1)), shell=True)
    ok_(ret_code == 0)

def test_turn_off_bitbucket_repo_hg():
    ret_code = subprocess.call("bep turn_off bitbucket {} --branch=default".format(repo_name(bitbucket_repo_hg)), shell=True)
    ok_(ret_code == 0)


def test_turn_on_github_repo1():
    ret_code = subprocess.call("bep turn_on github {} --branch=master".format(repo_name(github_repo1)), shell=True)
    ok_(ret_code == 0)


def test_update_github_repo1():
    ret_code = subprocess.call("bep update github {} --branch=master".format(repo_name(github_repo1)), shell=True)
    ok_(ret_code == 0)

def test_update_all():
    ret_code = subprocess.call("bep update --all", shell=True)
    ok_(ret_code == 0)


def test_list():
    ret_code = subprocess.call("bep list", shell=True)
    ok_(ret_code == 0)


def test_remove_github_repo1():
    ret_code = subprocess.call("bep remove github {} --branch=master".format(github_repo1), shell=True)
    ok_(ret_code == 0)

def test_remove_bitbucket_repo_hg():
    ret_code = subprocess.call("bep remove bitbucket {} --branch=default".format(repo_name(bitbucket_repo_hg)), shell=True)
    ok_(ret_code == 0)

def test_turn_off_all():
    ret_code = subprocess.call("bep turn_off --all", shell=True)
    ok_(ret_code == 0)

def test_turn_on_github_repo2():
    ret_code = subprocess.call("bep turn_off github {} --branch=master".format(repo_name(github_repo2)), shell=True)
    ok_(ret_code == 0)


# don't remove all in unit-tests; leave potentially already installed pkgs alone.
# def test_remove_all():
    # ret_code = subprocess.call("bep remove --all", shell=True)
    # ok_(ret_code == 0)

# only remove pkgs used to test during unit-testing
def test_remove_github_repo2():
    ret_code = subprocess.call("bep remove github {} --branch=master".format(github_repo2), shell=True)
    ok_(ret_code == 0)

def test_remove_bitbucket_repo_git():
    ret_code = subprocess.call("bep remove bitbucket {} --branch=master".format(repo_name(bitbucket_repo_git)), shell=True)
    ok_(ret_code == 0)
