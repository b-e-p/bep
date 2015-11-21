#!/usr/bin/env python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 11-19-2015
# Purpose:
#----------------------------------------------------------------

from Bep.core import utils


def list_cmd(everything_already_installed, noise):
    ''' Lists/writes all installed packages to stdout.

    Parameters
    ----------
    everything_already_installed:  dict of all installed packages by lang_version, pkg_type, pkg_name,
        and branches installed for that hierarchy.
    noise:  noise class inst with the verbosity level for the amount of output to deliver to stdout.
    '''

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
