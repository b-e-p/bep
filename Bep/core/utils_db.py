#!/usr/bin/python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 09-29-2013
# Purpose: general utilites used by the packages script
#----------------------------------------------------------------

import os
import json

def handle_db_after_an_install(pkg_type, pkg_to_install_name, branch_to_install,
                                    lang_cmd_for_install, db_pname):

    branch_to_install_dict = {'installation_lang_cmd': lang_cmd_for_install,
                             }

    if not os.path.exists(db_pname):
        with open(db_pname, 'w') as f:
            db = {pkg_type: {
                    pkg_to_install_name: {
                        branch_to_install: branch_to_install_dict
                            }}}
            json.dump(db, f, indent=4)

    elif os.path.exists(db_pname):
        with open(db_pname, 'r') as f:
            db = json.load(f)
            if pkg_type in db:
                if pkg_to_install_name in db[pkg_type]:
                    if branch_to_install in db[pkg_type][pkg_to_install_name]:
                        # this is for a branch back on if it was turned off
                        pass
                    else:  # then have to add branch_to_install
                        db[pkg_type][pkg_to_install_name].update({
                            branch_to_install: branch_to_install_dict
                                })
                else:  # then have to add pkg_to_install_name
                    db[pkg_type].update({
                            pkg_to_install_name: {
                                branch_to_install: branch_to_install_dict
                                    }})
            else:   # then have to add pkg_type
                db.update({
                    pkg_type: {
                        pkg_to_install_name: {
                            branch_to_install: branch_to_install_dict
                                }}})

        with open(db_pname, 'w') as f:
            json.dump(db, f, sort_keys=True, indent=4)



def get_lang_cmd_branch_was_installed_with(pkg_type, pkg_name, branch, db_pname):
    with open(db_pname, 'r') as f:
        db = json.load(f)
        lang_branch_installed_with = db[pkg_type][pkg_name][branch]['installation_lang_cmd']
        return lang_branch_installed_with




# TODO  make it so that it removes things appropriately in the db...
def handle_db_for_removal(pkg_type, pkg_to_remove_name, branch_to_remove, db_pname):

    if os.path.exists(db_pname):
        with open(db_pname, 'r') as f:
            db = json.load(f)
            if pkg_type in db:
                if pkg_to_remove_name in db[pkg_type]:
                    if branch_to_remove in db[pkg_type][pkg_to_remove_name]:
                        # remove the branch from the pkg_name, from the pkg_type
                        del db[pkg_type][pkg_to_remove_name][branch_to_remove]
                    else:
                        # branch is not here to remove
                        pass
                else:
                    # pkg_to_remove_name is not here to remove
                    pass
            else:
                # pkg_type is not here to remove
                pass

        for pkg_type, pkgs_to_remove_dict in db.items():
            if not pkgs_to_remove_dict:
                del db[pkg_type] # if the pkgs_to_remove_dict doesn't have anything in it, then remove it

            for pkg_to_remove, branches_to_remove_dict in pkgs_to_remove_dict.items():
                if not branches_to_remove_dict:
                    del db[pkg_type][pkg_to_remove] # if the branches_to_remove_dict doesn't have anything in it, then remove it


        with open(db_pname, 'w') as f:
            json.dump(db, f, sort_keys=True, indent=4)


def handle_db_for_branch_renaming(pkg_type, pkg_name, branch_orig_name, branch_renamed, db_pname):

    if os.path.exists(db_pname):
        with open(db_pname, 'r') as f:
            db = json.load(f)
            if pkg_type in db:
                if pkg_name in db[pkg_type]:
                    if branch_orig_name in db[pkg_type][pkg_name]:
                        # rename the branch key from the pkg_name, from the pkg_type
                         db[pkg_type][pkg_name][branch_renamed] = db[pkg_type][pkg_name].pop(branch_orig_name)
                    else:
                        # branch is not there
                        pass
                else:
                    # pkg_name is not there
                    pass
            else:
                # pkg_type is not there
                pass


        with open(db_pname, 'w') as f:
            json.dump(db, f, sort_keys=True, indent=4)
