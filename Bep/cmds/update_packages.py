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


def update_cmd(args, additional_args, lang_dir_name, pkg_type, noise, install_dirs,
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

