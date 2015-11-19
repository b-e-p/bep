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


def turn_on_cmd(args, additional_args, lang_dir_name, pkg_type, noise, install_dirs,
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

