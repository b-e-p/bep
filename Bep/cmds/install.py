#!/usr/bin/env python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 11-19-2015
# Purpose:
#----------------------------------------------------------------

import os
import sys
import imp

from Bep.core.release_info import name
from Bep.core import utils
from Bep import package



class Args(object):
    ''' Builds a namespace similar to if `args` were passed in on the cmdline (via argparse) '''
    def __init__(self, repo_type, pkg_type, pkg_to_install, language, branch):
        self.repo_type = repo_type
        self.pkg_type = pkg_type
        self.pkg_to_install = pkg_to_install
        self.branch = branch
        self.language = language


def install_cmd(args, packages_file, packages_file_path, noise, install_dirs, installed_pkgs_dir):
    ''' Installs package(s) for either cmdline install interface or from .bep_packages file install

    Parameters
    ----------
    args:  a class inst of the argparse namespace with the arguments parsed to use during the install.
    packages_file:  the user's .bep_packages file.
    packages_file_path:  the absolute path to the packages_file.
    noise:  noise class inst with the verbosity level for the amount of output to deliver to stdout.
    install_dirs:  dict of install locations for installed pkgs and install logs.
    installed_pkgs_dir:  the absolute path to the where the downloaded and built pkgs are stored.
    '''

    ##### install from packages file    # FIXME --this is hacky -- fix this
    #if ('pkg_type' in args) and (args.pkg_type == "packages"):
    if args.pkg_type == "packages":
        try:  # bring in the packages file
            sys.dont_write_bytecode = True  # to avoid writing a .pyc files (for the packages file)
            pkgs_module = imp.load_source(packages_file, packages_file_path)    # used to import a hidden file (really hackey)
        except (ImportError, IOError):
            print("No {0} file installed for use.".format(packages_file))
            if not os.path.isfile(packages_file_path):  # create packages file if one doesn't already exist.
                #shutil.copy(join('data', packages_file), packages_file_path)    # create a template packages file
                #print("So created template {0} file for installation of packages.".format(packages_file))

                open(packages_file_path, 'a').close()  # creates an empty packages file
                print("So created empty {0} file for installation of packages.".format(packages_file))

            raise SystemExit("Now add the desired packages to the {} file and re-run install.".format(packages_file))



        def raise_problem(pkg_to_install):
            print("\nError: cannot process entry in {}:".format(packages_file))
            print("\t{}\n".format(pkg_to_install))
            print("Item needs to be specified like such:")
            print("\t{} [language-->]repoType+userName/packageName[^branch]".format(name))
            print("\nNote: language and branch are both optional, and repoType only needs")
            print("to be specified if it's not ambigious given where the package comes from:")
            print("\teg. for a github install:  ipython/ipython")
            print("\teg. for a github install:  python3.3-->ipython/ipython")
            print("\teg. for a bitbucket install:  hg+mchaput/whoosh")
            print("\teg. for a local install:  git+/home/username/path/to/repo")
            raise SystemExit


        for pkg_type, pkgs_from_pkgs_file in pkgs_module.packages.items():
            utils.when_not_quiet_mode(utils.status('\t\tInstalling {0} packages'.format(pkg_type)), noise.quiet)

            if pkgs_from_pkgs_file:

                #####################################################################################################
                # FIXME need to refractor what the packages file is (or refractor this here)
                for pkg_to_install_entry in pkgs_from_pkgs_file:

                    lang_N_repo_type_N_pkg_to_install_N_branch = pkg_to_install_entry.split('-->')  # to see if a language is given
                    if len(lang_N_repo_type_N_pkg_to_install_N_branch) == 2:
                        lang_arg, repo_type_N_pkg_to_install_N_branch = lang_N_repo_type_N_pkg_to_install_N_branch

                        repo_type_N_pkg_to_install_N_branch = repo_type_N_pkg_to_install_N_branch.split('+')    # to see if repo_type given # NOTE this won't work for pypi pkgs b/c there won't be a repo
                        if len(repo_type_N_pkg_to_install_N_branch) == 2:
                            repo_type, pkg_to_install_N_branch = repo_type_N_pkg_to_install_N_branch

                            pkg_to_install_N_branch = pkg_to_install_N_branch.split('^')    # to see if branch is given
                            if len(pkg_to_install_N_branch) == 2:
                                pkg_to_install, branch = pkg_to_install_N_branch
                                legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                if legit_pkg_name:
                                    args = Args(repo_type, pkg_type, pkg_to_install, language=lang_arg, branch=branch)
                                else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                    raise_problem(pkg_to_install_entry)
                            elif len(pkg_to_install_N_branch) == 1:     # if branch not given, then get default #NOTE won't work for pypi installs
                                pkg_to_install = pkg_to_install_N_branch[0]
                                legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                if legit_pkg_name:
                                    branch = utils.get_default_branch(repo_type)
                                    args = Args(repo_type, pkg_type, pkg_to_install, language=lang_arg, branch=branch) # use default branch
                                else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                    raise_problem(pkg_to_install_entry)
                            else:   # if too many ^ given
                                raise_problem(pkg_to_install_entry)

                        elif len(repo_type_N_pkg_to_install_N_branch) == 1:     # if repo_type not given
                            pkg_to_install_N_branch = repo_type_N_pkg_to_install_N_branch[0]
                            if pkg_type in ['github']:
                                repo_type = 'git'

                                pkg_to_install_N_branch = pkg_to_install_N_branch.split('^')    # to see if branch is given
                                if len(pkg_to_install_N_branch) == 2:
                                    pkg_to_install, branch = pkg_to_install_N_branch
                                    legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                    if legit_pkg_name:
                                        args = Args(repo_type, pkg_type, pkg_to_install, branch=branch, language=lang_arg)
                                    else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                        raise_problem(pkg_to_install_entry)
                                elif len(pkg_to_install_N_branch) == 1:     # if branch not given, then get default #NOTE won't work for pypi installs
                                    pkg_to_install = pkg_to_install_N_branch[0]
                                    legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                    if legit_pkg_name:
                                        branch = utils.get_default_branch(repo_type)
                                        args = Args(repo_type, pkg_type, pkg_to_install, language=lang_arg, branch=branch) # use default branch
                                    else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                        raise_problem(pkg_to_install_entry)
                                else:   # if too many ^ given
                                    raise_problem(pkg_to_install_entry)
                            else:   # if ambigious repo_type (w/ more than one repo_type possible)
                                raise_problem(pkg_to_install_entry)
                        else:   # if too many '+'  given
                            raise_problem(pkg_to_install_entry)

                    elif len(lang_N_repo_type_N_pkg_to_install_N_branch) == 1:  # language not given, use system default lang
                        repo_type_N_pkg_to_install_N_branch = lang_N_repo_type_N_pkg_to_install_N_branch[0]

                        repo_type_N_pkg_to_install_N_branch = repo_type_N_pkg_to_install_N_branch.split('+')    # to see if repo_type given # FIXME this won't work for pypi pkgs b/c there won't be a repo
                        if len(repo_type_N_pkg_to_install_N_branch) == 2:
                            repo_type, pkg_to_install_N_branch = repo_type_N_pkg_to_install_N_branch

                            pkg_to_install_N_branch = pkg_to_install_N_branch.split('^')    # to see if branch is given
                            if len(pkg_to_install_N_branch) == 2:
                                pkg_to_install, branch = pkg_to_install_N_branch
                                legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                if legit_pkg_name:
                                    args = Args(repo_type, pkg_type, pkg_to_install, language=args.language, branch=branch)     # use default language
                                else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                    raise_problem(pkg_to_install_entry)
                            elif len(pkg_to_install_N_branch) == 1:     # if branch not given, then get default #FIXME won't work for pypi installs
                                pkg_to_install = pkg_to_install_N_branch[0]
                                legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                if legit_pkg_name:
                                    branch = utils.get_default_branch(repo_type)
                                    args = Args(repo_type, pkg_type, pkg_to_install, language=args.language, branch=branch)    # use default language & branch,
                                else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                    raise_problem(pkg_to_install_entry)
                            else:   # if too many ^ given
                                raise_problem(pkg_to_install_entry)

                        elif len(repo_type_N_pkg_to_install_N_branch) == 1:     # if repo_type not given
                            pkg_to_install_N_branch = repo_type_N_pkg_to_install_N_branch[0]
                            if pkg_type in ['github']:
                                repo_type = 'git'

                                pkg_to_install_N_branch = pkg_to_install_N_branch.split('^')    # to see if branch is given
                                if len(pkg_to_install_N_branch) == 2:
                                    pkg_to_install, branch = pkg_to_install_N_branch
                                    legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                    if legit_pkg_name:
                                        args = Args(repo_type, pkg_type, pkg_to_install, language=args.language, branch=branch)     # use default language
                                    else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                        raise_problem(pkg_to_install_entry)
                                elif len(pkg_to_install_N_branch) == 1:     # if branch not given, then get default #FIXME won't work for pypi installs
                                    pkg_to_install = pkg_to_install_N_branch[0]
                                    legit_pkg_name = utils.check_if_valid_pkg_to_install(pkg_to_install, pkg_type)
                                    if legit_pkg_name:
                                        branch = utils.get_default_branch(repo_type)
                                        args = Args(repo_type, pkg_type, pkg_to_install, language=args.language, branch=branch)    # use default language & branch,
                                    else:   # not a legit pkg_to_install in the pkg_to_install_entry
                                        raise_problem(pkg_to_install_entry)
                                else:   # if too many ^ given
                                    raise_problem(pkg_to_install_entry)
                            else:   # if ambigious repo_type (w/ more than one repo_type possible)
                                raise_problem(pkg_to_install_entry)
                        else:   # if too many '+'  given
                            raise_problem(pkg_to_install_entry)
                    else:   # if not one or two items after "-->" split
                        raise_problem(pkg_to_install_entry)
                    #####################################################################################################

                    # important to see what has previously been installed, so as to not turn on a 2nd version of a package.
                    everything_already_installed = utils.all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir)

                    pkg_inst = package.create_pkg_inst(args.language, args.pkg_type, install_dirs, args=args) # args are created from the Args class here, unlike where args are the cmdline options for every other action
                    pkg_inst.install(args.pkg_to_install, args, noise, everything_already_installed=everything_already_installed)
            else:
                utils.when_not_quiet_mode('\nNo {0} packages specified in {1} to install.'.format(pkg_type, packages_file), noise.quiet)


    #### install w/ command line arg(s)
    #if 'pkg_to_install' in args:
    else:

        utils.when_not_quiet_mode(utils.status('\t\tInstalling {0} package'.format(args.pkg_type)), noise.quiet)

        pkg_inst = package.create_pkg_inst(args.language, args.pkg_type, install_dirs, args=args)

        # important to keep this here so it can be known what has previously been installed, so as to not turn on a 2nd version of a package.
        everything_already_installed = utils.all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir)
        pkg_inst.install(args.pkg_to_install, args, noise, everything_already_installed=everything_already_installed)

