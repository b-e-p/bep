#!/usr/bin/python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 03-28-2014
# Purpose:
#----------------------------------------------------------------

import os
import sys
import imp

from Bep.core.release_info import name
from Bep.core import utils
from Bep import package



class Args(object):
    ''' create a namespace similar to if "args" that were passed in on cmdline '''
    def __init__(self, repo_type, pkg_type, pkg_to_install, language, branch):
        self.repo_type = repo_type
        self.pkg_type = pkg_type
        self.pkg_to_install = pkg_to_install
        self.branch = branch
        self.language = language



def install_action(args, packages_file, packages_file_path, noise, install_dirs, installed_pkgs_dir):

    ##### install from packages file    # FIXME --this is really, really hacky -- fix this garbage!
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
                # FIXME this is embarassing & complete unmaintainable garbage....seriously need to refractor what the
                # packages file is (or at minimum refractor this shitty garbage here)
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



def list_action(everything_already_installed, noise):

    for lang_dir_name, pkg_type_dict in everything_already_installed.items():

        utils.when_not_quiet_mode("\n{0} packages installed:".format(lang_dir_name), noise.quiet)

        for pkg_type, pkgs_and_branches in pkg_type_dict.items():
            #if pkgs_and_branches:  # don't think i need this

            def list_packages():
                any_pkg_listed = False
                for pkg_for_listing, branches in pkgs_and_branches.items():
                    for branch in branches:
                        if branch.startswith('.__'):
                            branch_if_were_on = branch.lstrip('.__')
                            branch_if_were_on = '[{0}]'.format(branch_if_were_on)
                            item_installed = '  {: >20} {: >25} {: >25} {: >10}'.format(pkg_for_listing, branch_if_were_on, pkg_type, "** off")

                        elif not branch.startswith('.__'):
                            branch = '[{0}]'.format(branch)
                            item_installed = '  {: >20} {: >25} {: >25}'.format(pkg_for_listing, branch, pkg_type)
                        any_pkg_listed = True
                        print(item_installed)
                return any_pkg_listed

            any_pkg_listed = list_packages()

    if not any_pkg_listed:
        utils.when_not_quiet_mode('\n[ No packages for listing ]'.format(pkg_type), noise.quiet)





command_and_items_to_process_when_multiple_items = {}   # but not for install command


def update_action(args, additional_args, lang_dir_name, pkg_type, noise, install_dirs,
                  pkgs_and_branches_on, pkgs_and_branches_off, everything_already_installed, **kwargs):

    if 'all' in args :
        msg = '\t\tUpdating {0} {1} packages'.format(lang_dir_name, pkg_type)
        utils.when_not_quiet_mode(utils.status(msg), noise.quiet)
        pkg_inst = package.create_pkg_inst(lang_dir_name, pkg_type, install_dirs, args=args)

        any_pkg_updated = False
        for pkg_to_update, branch_on in pkgs_and_branches_on.items():
            for branch_to_update in branch_on:
                pkg_inst.update(lang_dir_name, pkg_to_update, branch_to_update, noise)
                any_pkg_updated = True

        if any_pkg_updated:
            return True
        else:
            msg = '\nNo {0} {1} packages turned on for updating.'.format(lang_dir_name, pkg_type)
            utils.when_not_quiet_mode(msg, noise.quiet)
            return False


    else: # for a single command passed to update
        # a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's updated.

        def how_to_update_branches(pkg_to_update, all_installed_for_pkg):
            any_how_to_displayed = False
            for quad_tuple in all_installed_for_pkg:
                lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
                if (lang_installed == lang_dir_name) and (pkg_type_installed == pkg_type):

                    if branch_installed.startswith('.__'):
                        branch_installed = branch_installed.lstrip('.__')
                        #print("\n# {0} [{1}] {2} turned off:  turn on to update.".format(#pkg_name_installed, branch_installed, lang_installed))
                        update_cue = "{0} [{1}] {2} turned off:".format(
                                                            pkg_name_installed, branch_installed, lang_installed)
                        update_cmd = "**** Must turn on to update ****"
                    elif not branch_installed.startswith('.__'):
                        #if branch_installed == 'master':
                            ##print("\n# Update {0} {1} with:".format(pkg_to_update, lang_installed))
                            ##print("{0} -l {1} update {2} {3}".format(name, lang_installed,
                                                    ##pkg_type_installed, pkg_name_installed))
                            #update_cue = "Update {0} {1} with:".format(pkg_to_update, lang_installed)
                            #update_cmd = "{0} -l {1} update {2} {3}".format(name, lang_installed,
                                                    #pkg_type_installed, pkg_name_installed)

                        #else:
                            ##print("\n# Update {0} [{1}] {2} with:".format(pkg_to_update, branch_installed, lang_installed))
                            ##print("{0} -l {1} update {2} {3} --branch={4}".format(name, lang_installed, pkg_type_installed, pkg_name_installed, branch_installed))
                            #update_cue = "Update {0} [{1}] {2} with:".format(pkg_to_update, branch_installed, lang_installed)
                            #update_cmd = "{0} -l {1} update {2} {3} --branch={4}".format(name, lang_installed,
                                                    #pkg_type_installed, pkg_name_installed, branch_installed)
                        update_cue = "Update {0} [{1}] {2} with:".format(pkg_to_update, branch_installed, lang_installed)
                        update_cmd = "{0} -l {1} update {2} {3} --branch={4}".format(name, lang_installed,
                                                pkg_type_installed, pkg_name_installed, branch_installed)
                    command_and_items_to_process_when_multiple_items[update_cue] = update_cmd
                    any_how_to_displayed = True

            if any_how_to_displayed:
                #return True
                return command_and_items_to_process_when_multiple_items
            else:
                return False


        def update_branch(lang_arg, pkg_to_update, branch_to_update):
            a_pkg_was_processed = False
            pkg_inst = package.create_pkg_inst(lang_arg, pkg_type, install_dirs)
            lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
            if lang_dir_name == lang_cmd:

                if pkg_to_update in pkgs_and_branches_on:   # a dict w/ pkg_to_update key and value is branch_on list (w/ only 1 item in the list b/c only 1 branch can be on)
                    branch_on = pkgs_and_branches_on[pkg_to_update]
                    if branch_to_update in branch_on:
                        utils.when_not_quiet_mode(utils.status('\tUpdating {0} [{1}] {2} {3}'.format(
                                pkg_to_update, branch_to_update, lang_dir_name, pkg_type)), noise.quiet)
                        pkg_inst.update(lang_cmd, pkg_to_update, branch_to_update, noise)
                        a_pkg_was_processed = True

                if pkg_to_update in pkgs_and_branches_off:   # a dict w/ pkg_to_update key and value is branch_off list (many branches could be off)
                    branches_off = pkgs_and_branches_off[pkg_to_update]
                    if branch_to_update in branches_off:
                        branch_installed = branch_to_update.lstrip('.__')
                        print("\n{0} [{1}] {2} turned off:  turn on to update.".format(
                                                            pkg_to_update, branch_installed, lang_cmd))
                        a_pkg_was_processed = True


                if a_pkg_was_processed:
                    return True
                else:
                    return False


        pkg_was_processed_or_displayed = utils.package_processor(args,
                                                additional_args,
                                                pkg_type,
                                                how_to_func=how_to_update_branches,
                                                processing_func=update_branch,
                                                process_str='update',
                                                everything_already_installed=everything_already_installed,
                                                )

        # pkg_was_processed_or_displayed will be either:
        # A.  how_to_func -- False or a dict containing actions to take
        #       (False being that no packages were caught in the how_to_func, True being that at least 1 package was found)
        # B.  processing_func -- True or False
        #       (True being that a package was found in processing_func (updated or not) and False means none were found)
        #if pkg_was_processed_or_displayed:  # this is what gets return back into the run script
            #return True
        #else:
            #return False
        return pkg_was_processed_or_displayed



def remove_action(args, additional_args, lang_dir_name, pkg_type, noise, install_dirs,
                  pkgs_and_branches_on, pkgs_and_branches_off, everything_already_installed, **kwargs):


    def remove_pkg_branches(which_pkgs_and_branches_to_remove, branches_type):
        any_pkg_off_removed = False
        for pkg_to_remove, branches in which_pkgs_and_branches_to_remove.items():
            for branch_to_remove in branches:
                if branches_type == 'off':
                    branch_to_remove = '.__{0}'.format(branch_to_remove)
                pkg_inst.remove(pkg_to_remove, branch_to_remove, noise)
                any_pkg_off_removed = True
        return any_pkg_off_removed


    if 'all' in args:
        utils.when_not_quiet_mode(utils.status('\t\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
        pkg_inst = package.create_pkg_inst(lang_dir_name, pkg_type, install_dirs)
        any_pkg_on_removed = remove_pkg_branches(pkgs_and_branches_on, branches_type='on')
        any_pkg_off_removed = remove_pkg_branches(pkgs_and_branches_off, branches_type='off')
        if (any_pkg_on_removed or any_pkg_off_removed):
            return True
        else:
            return False


    #elif remove_arg == 'turned_off':   # NOTE this would require that another flag be passed to the remove cmd (--turned_off, just like --all)
        #utils.when_not_quiet_mode(utils.status('\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
        #pkg_inst = create_pkg_inst(lang_dir_name, pkg_type, install_dirs)
        #count_of_pkgs_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
        #if count_of_pkgs_removed == 0:
            #utils.when_not_quiet_mode('\nNo {0} {1} packages turned off for removal.'.format(lang_dir_name, pkg_type), noise.quiet)
            #top_count_of_pkgs_removed = -1


    else: # for a single command passed to remove
        # a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's removed

        def how_to_remove_branches(pkg_to_remove, all_installed_for_pkg):
            any_how_to_displayed = False
            for quad_tuple in all_installed_for_pkg:
                lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
                if (lang_installed == lang_dir_name) and (pkg_type_installed == pkg_type):
                    if branch_installed.startswith('.__'):
                        branch_installed = branch_installed.lstrip('.__')
                    #if branch_installed == 'master':
                        ##print("\n# Remove {0} {1} with:".format(pkg_to_remove, lang_installed))
                        ##print("{0} -l {1} remove {2}={3}".format(name, lang_installed, pkg_type_installed, pkg_name_installed))
                        #remove_cue = "Remove {0} {1} with:".format(pkg_to_remove, lang_installed)
                        #remove_cmd = "{0} -l {1} remove {2} {3}".format(name, lang_installed,
                                                #pkg_type_installed, pkg_name_installed)
                    #else:
                        ##print("\n# Remove {0} [{1}] {2} with:".format(pkg_to_remove, branch_installed, lang_installed))
                        ##print("{0} -l {1} remove {2}={3}^{4}".format(name, lang_installed, pkg_type_installed, pkg_name_installed, branch_installed))
                        #remove_cue = "Remove {0} [{1}] {2} with:".format(pkg_to_remove, branch_installed, lang_installed)
                        #remove_cmd = "{0} -l {1} remove {2} {3} --branch={4}".format(name, lang_installed,
                                                #pkg_type_installed, pkg_name_installed, branch_installed)
                    remove_cue = "Remove {0} [{1}] {2} with:".format(pkg_to_remove, branch_installed, lang_installed)
                    remove_cmd = "{0} -l {1} remove {2} {3} --branch={4}".format(name, lang_installed,
                                            pkg_type_installed, pkg_name_installed, branch_installed)
                    command_and_items_to_process_when_multiple_items[remove_cue] = remove_cmd
                    any_how_to_displayed = True

            if any_how_to_displayed:
                #return True
                return command_and_items_to_process_when_multiple_items
            else:
                return False


        def remove_branch(lang_arg, pkg_to_remove, branch_to_remove):

            pkg_inst = package.create_pkg_inst(lang_arg, pkg_type, install_dirs)
            lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
            if lang_dir_name == lang_cmd:

                def _remove(which_pkgs_and_branches_to_remove, branches_type, branch_to_remove=branch_to_remove):
                    if pkg_to_remove in which_pkgs_and_branches_to_remove:
                        branches_installed = which_pkgs_and_branches_to_remove[pkg_to_remove]   # if which_pkgs_and_branches_to_remove are pkgs_and_branches_on, then branches_installed will be a list of only 1 item
                        if branch_to_remove in branches_installed:
                            utils.when_not_quiet_mode(utils.status('\tRemoving {0} [{1}] {2} {3}'.format(
                                        pkg_to_remove, branch_to_remove, lang_dir_name, pkg_type)), noise.quiet)
                            if branches_type == 'off':
                                branch_to_remove = '.__{0}'.format(branch_to_remove)
                            pkg_inst.remove(pkg_to_remove, branch_to_remove, noise)
                            return True
                    else:
                        return False

                a_pkg_on_was_processed = _remove(pkgs_and_branches_on, branches_type='on')
                a_pkg_off_was_processed = _remove(pkgs_and_branches_off, branches_type='off')

                if (a_pkg_on_was_processed or a_pkg_off_was_processed):
                    return True
                else:
                    return False



        pkg_was_processed_or_displayed = utils.package_processor(args,
                                                additional_args,
                                                pkg_type,
                                                how_to_func=how_to_remove_branches,
                                                processing_func=remove_branch,
                                                process_str='remove',
                                                everything_already_installed=everything_already_installed,
                                                )

        return pkg_was_processed_or_displayed



def turn_off_action(args, additional_args, lang_dir_name, pkg_type, noise, install_dirs,
                  pkgs_and_branches_on, pkgs_and_branches_off, everything_already_installed, **kwargs):


    def turn_off_branches():
        any_pkg_turned_off = False
        for pkg_to_turn_off, branch_on in pkgs_and_branches_on.items():
            if pkg_to_turn_off == name:  # don't allow this package manager to turn itself off
                print("\n**** Cannot use {name} to turn off {name} ****".format(name=name))
                continue

            for branch_to_turn_off in branch_on:
                pkg_inst.turn_off(pkg_to_turn_off, branch_to_turn_off, noise)
                any_pkg_turned_off = True
        return any_pkg_turned_off


    if 'all' in args :
        msg = '\t\tTurning off {0} {1} packages'.format(lang_dir_name, pkg_type)
        utils.when_not_quiet_mode(utils.status(msg), noise.quiet)
        pkg_inst = package.create_pkg_inst(lang_dir_name, pkg_type, install_dirs)

        any_pkg_turned_off = turn_off_branches()
        if any_pkg_turned_off:
            return True
        else:
            msg = '\nNo {0} {1} packages turned on.'.format(lang_dir_name, pkg_type)
            utils.when_not_quiet_mode(msg, noise.quiet)
            return False

    else: # for a single command passed to turn off
        # a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's turned off

        def how_to_turn_off_branches(pkg_to_turn_off, all_installed_for_pkg):
            any_how_to_displayed = False
            for quad_tuple in all_installed_for_pkg:
                lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
                if (lang_installed == lang_dir_name) and (pkg_type_installed == pkg_type):

                    if branch_installed.startswith('.__'):
                        branch_installed = branch_installed.lstrip('.__')
                        #print("\n* {0} [{1}] {2} already turned off.".format(pkg_name_installed, branch_installed, lang_installed))
                        turn_off_cue = "{0} [{1}] {2} already turned off.".format(pkg_name_installed, branch_installed, lang_installed)
                        turn_off_cmd = "**** Already turned off ****"

                    elif not branch_installed.startswith('.__'):
                        #if branch_installed == 'master':
                            ##print("\n# Turn off {0} {1} with:".format(pkg_to_turn_off, lang_installed))
                            ##print("{0} -l {1} turn_off {2}={3}".format(name, lang_installed, pkg_type_installed, pkg_name_installed))
                            #turn_off_cue = "Turn off {0} {1} with:".format(pkg_to_turn_off, lang_installed)
                            #turn_off_cmd = "{0} -l {1} turn_off {2} {3}".format(name, lang_installed,
                                                    #pkg_type_installed, pkg_name_installed)
                        #else:
                            ##print("\n# Turn off {0} [{1}] {2} with:".format(pkg_to_turn_off, branch_installed, lang_installed))
                            ##print("{0} -l {1} turn_off {2}={3}^{4}".format(name, lang_installed, pkg_type_installed, pkg_name_installed, branch_installed))
                            #turn_off_cue = "Turn off {0} [{1}] {2} with:".format(pkg_to_turn_off, branch_installed, lang_installed)
                            #turn_off_cmd = "{0} -l {1} turn_off {2} {3} --branch={4}".format(name, lang_installed,
                                                    #pkg_type_installed, pkg_name_installed, branch_installed)
                        turn_off_cue = "Turn off {0} [{1}] {2} with:".format(pkg_to_turn_off, branch_installed, lang_installed)
                        turn_off_cmd = "{0} -l {1} turn_off {2} {3} --branch={4}".format(name, lang_installed,
                                                pkg_type_installed, pkg_name_installed, branch_installed)
                    command_and_items_to_process_when_multiple_items[turn_off_cue] = turn_off_cmd
                    any_how_to_displayed = True

            if any_how_to_displayed:
                #return True
                return command_and_items_to_process_when_multiple_items
            else:
                return False


        def turn_off_branch(lang_arg, pkg_to_turn_off, branch_to_turn_off):

            a_pkg_was_processed = False
            pkg_inst = package.create_pkg_inst(lang_arg, pkg_type, install_dirs)
            lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
            if lang_dir_name == lang_cmd:

                if pkg_to_turn_off in pkgs_and_branches_on:
                    branch_on = pkgs_and_branches_on[pkg_to_turn_off]

                    if pkg_to_turn_off == name:  # don't allow this package manager to turn itself off
                        print("\n**** Cannot use {name} to turn off {name} ****".format(name=name))
                        return True

                    if branch_to_turn_off in branch_on:     # there will only be one branch in branch_on list
                        utils.when_not_quiet_mode(utils.status('\tTurning off {0} [{1}] {2} {3}'.format(
                                pkg_to_turn_off, branch_to_turn_off, lang_dir_name, pkg_type)), noise.quiet)
                        pkg_inst.turn_off(pkg_to_turn_off, branch_to_turn_off, noise)
                        a_pkg_was_processed = True

                if pkg_to_turn_off in pkgs_and_branches_off:
                    branches_off = pkgs_and_branches_off[pkg_to_turn_off]
                    if branch_to_turn_off in branches_off:
                        #branch_installed = branch_to_turn_off.lstrip('.__')
                        print('\n{0} [{1}] {2} already turned off.'.format(pkg_to_turn_off, branch_to_turn_off, lang_cmd))
                        a_pkg_was_processed = True


                if a_pkg_was_processed:
                    return True
                else:
                    return False

        pkg_was_processed_or_displayed = utils.package_processor(args,
                                                additional_args,
                                                pkg_type,
                                                how_to_func=how_to_turn_off_branches,
                                                processing_func=turn_off_branch,
                                                process_str='turn_off',
                                                everything_already_installed=everything_already_installed,
                                                )

        return pkg_was_processed_or_displayed



def turn_on_action(args, additional_args, lang_dir_name, pkg_type, noise, install_dirs,
                  pkgs_and_branches_on, pkgs_and_branches_off, everything_already_installed, **kwargs):

    # only a single item can be turned on at any given time, so this is for a single command passed to turn_on.
    # (a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's turned on)

    def how_to_turn_on_branches(pkg_to_turn_on, all_installed_for_pkg):
        any_how_to_displayed = False
        for quad_tuple in all_installed_for_pkg:
            lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
            if (lang_installed == lang_dir_name) and (pkg_type_installed == pkg_type):
                if branch_installed.startswith('.__'):
                    branch_installed = branch_installed.lstrip('.__')
                    #if branch_installed == 'master':
                        ##print("\n# Turn on {0} {1} with:".format(pkg_to_turn_on, lang_installed))
                        ##print("{0} -l {1} turn_on {2}={3}".format(name, lang_installed, pkg_type_installed, pkg_name_installed))
                        #turn_on_cue = "Turn on {0} {1} with:".format(pkg_to_turn_on, lang_installed)
                        #turn_on_cmd = "{0} -l {1} turn_on {2} {3}".format(name, lang_installed,
                                                #pkg_type_installed, pkg_name_installed)
                    #else:
                        ##print("\n# Turn on {0} [{1}] {2} with:".format(pkg_to_turn_on, branch_installed, lang_installed))
                        ##print("{0} -l {1} turn_on {2}={3}^{4}".format(name, lang_installed, pkg_type_installed, pkg_name_installed, branch_installed))
                        #turn_on_cue = "Turn on {0} [{1}] {2} with:".format(pkg_to_turn_on, branch_installed, lang_installed)
                        #turn_on_cmd = "{0} -l {1} turn_on {2} {3} --branch={4}".format(name, lang_installed,
                                                #pkg_type_installed, pkg_name_installed, branch_installed)
                    turn_on_cue = "Turn on {0} [{1}] {2} with:".format(pkg_to_turn_on, branch_installed, lang_installed)
                    turn_on_cmd = "{0} -l {1} turn_on {2} {3} --branch={4}".format(name, lang_installed,
                                            pkg_type_installed, pkg_name_installed, branch_installed)

                elif not branch_installed.startswith('.__'):
                    #print("\n* {0} [{1}] {2} already turned on.".format(pkg_name_installed, branch_installed, lang_installed))
                    turn_on_cue = "{0} [{1}] {2} already turned on.".format(pkg_name_installed, branch_installed, lang_installed)
                    turn_on_cmd = "**** Already turned on ****"

                command_and_items_to_process_when_multiple_items[turn_on_cue] = turn_on_cmd
                any_how_to_displayed = True

        if any_how_to_displayed:
            #return True
            return command_and_items_to_process_when_multiple_items
        else:
            return False


    def turn_on_branch(lang_arg, pkg_to_turn_on, branch_to_turn_on):

        a_pkg_was_processed = False
        pkg_inst = package.create_pkg_inst(lang_arg, pkg_type, install_dirs)
        lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
        if lang_dir_name == lang_cmd:

            if pkg_to_turn_on in pkgs_and_branches_on:
                branch_on = pkgs_and_branches_on[pkg_to_turn_on]
                if branch_to_turn_on in branch_on:
                    print('\n{0} [{1}] {2} already turned on.'.format(pkg_to_turn_on, branch_to_turn_on, lang_cmd))
                    a_pkg_was_processed = True

            if pkg_to_turn_on in pkgs_and_branches_off:
                branches_off = pkgs_and_branches_off[pkg_to_turn_on]
                if branch_to_turn_on in branches_off:
                    utils.when_not_quiet_mode(utils.status('\tTurning on {0} [{1}] {2} {3}'.format(
                            pkg_to_turn_on, branch_to_turn_on, lang_dir_name, pkg_type)), noise.quiet)
                    branch_to_turn_on = '.__{0}'.format(branch_to_turn_on)
                    pkg_inst.turn_on(pkg_to_turn_on, branch_to_turn_on, args, everything_already_installed, noise)
                    a_pkg_was_processed = True

            if a_pkg_was_processed:
                return True
            else:
                return False


    pkg_was_processed_or_displayed = utils.package_processor(args,
                                            additional_args,
                                            pkg_type,
                                            how_to_func=how_to_turn_on_branches,
                                            processing_func=turn_on_branch,
                                            process_str='turn_on',
                                            everything_already_installed=everything_already_installed,
                                            )

    return pkg_was_processed_or_displayed

