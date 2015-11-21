#!/usr/bin/env python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 11-19-2015
# Purpose:
#----------------------------------------------------------------

from Bep.core.release_info import name
from Bep.core import utils
from Bep import package


command_and_items_to_process_when_multiple_items = {}   # but not for install command


def turn_off_cmd(args, additional_args, lang_dir_name, pkg_type, noise, install_dirs,
                  pkgs_and_branches_on, pkgs_and_branches_off, everything_already_installed, **kwargs):
    ''' Turns off specified packages.

    Parameters
    ----------
    args:  a class inst of the argparse namespace with the arguments parsed to use during the install.
    additional_args:  list of additional args parsed from the the argparse arguments.
    lang_dir_name:  name of lang_version dir for package to remove.
    pkg_type:  str of pkg_type to remove.
    noise:  noise class inst with the verbosity level for the amount of output to deliver to stdout.
    install_dirs:  dict of install locations for installed pkgs and install logs.
    pkgs_and_branches_on:  dict of all packages and branches currently turned on for this lang_version
        and pkg_type. eg. {'ipython': ['master']}
    pkgs_and_branches_off:  dict of all packages and branches currently turned off for this lang_version
        and pkg_type.
    everything_already_installed:  dict of all installed packages by lang_version, pkg_type, pkg_name,
        and branches installed for that hierarchy.

    '''


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


