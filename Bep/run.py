#! /usr/bin/env python

"""
#----------------------------------------------------------------
Author: Jason Gors <jasonDOTgorsATgmail>
Creation Date: 07-30-2013
Purpose: this manages installation of packages -- currently: git repos from github &
        gitorious; git & hg repos from bitbucket; git, hg & bzr local repos.  
#----------------------------------------------------------------
"""

import argparse
import os
from os.path import join
import sys 
import imp
import Bep.core.usage as usage 
from Bep.core.release_info import __version__, name
#from core.utils_db import (handle_db_after_an_install, handle_db_for_removal,
                        #handle_db_for_branch_renaming,
                        #get_lang_cmd_branch_was_installed_with)
import package
import utils


def create_pkg_inst(lang_arg, pkg_type, install_dirs, packages_file=None):
    ''' install_dirs is a dict '''

    if pkg_type == 'github':
        return package.Github(lang_arg, pkg_type, install_dirs)

    elif pkg_type == 'bitbucket':
        return package.Bitbucket(lang_arg, pkg_type, install_dirs)

    elif pkg_type == 'gitorious':
        return package.Gitorious(lang_arg, pkg_type, install_dirs)

    elif pkg_type == 'local_repo':
        return package.Local_Repo(lang_arg, pkg_type, install_dirs)

    elif pkg_type == 'stable':
        return package.Stable(lang_arg, pkg_type, install_dirs)

    # NOTE for future pkg_types
    #elif pkg_type == <new/different_pkg_type>:
        #pkg_inst = new/different_pkg_type(lang_arg, pkg_type)
        #return pkg_inst

    if packages_file:  # installs from the pkgs file are the only thing that get this argument 
        not_pkg_type = utils.status('{0} in your {1} is an unrecognized package type.\n'.format(pkg_type, packages_file))
        raise SystemExit(not_pkg_type)
    else:
        not_pkg_type = utils.status('{0} is an unrecognized package type.\n'.format(pkg_type))
        raise SystemExit(not_pkg_type)



usr_home_dir = os.path.expanduser('~')  # specifies the user's home dir  

#top_level_dir = join(options['top_level_dir'], '.{}'.format(name))
top_level_dir = join(usr_home_dir, '.{}'.format(name))

installed_pkgs_dir = join(top_level_dir, 'installed_pkgs') 
install_logs_dir = join(top_level_dir, '.install_logs') 
install_dirs = dict(installed_pkgs_dir=installed_pkgs_dir, install_logs_dir=install_logs_dir)

#installation_db = 'installation_db.json'
#installation_db_path = join(top_level_dir, installation_db)

packages_file = '.{}_packages'.format(name)
packages_file_path = join(usr_home_dir, packages_file)


def main(): # needs to be done as a main func for setuptools to work correctly in creating an executable
    
    parser = argparse.ArgumentParser(description=name.upper(),
                            formatter_class=argparse.RawDescriptionHelpFormatter,
                            epilog=usage.epilog_use)

    parser.add_argument('--version', action='version', version='%(prog)s {0}'.format(__version__))
    parser.add_argument('--language', '-l', nargs='?', default=None, help=usage.lang_use)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", help=usage.verbose_use)
    group.add_argument("-q", "--quiet", action="store_true", help=usage.quiet_use)


    subparsers = parser.add_subparsers(title='subcommands', description='(commands that %(prog)s uses)',
                                            help=usage.subparser_use)


    ### create parser for the "list" command
    # TODO make is so that:
    # can list all branches installed for a specific pkg,
    parser_list = subparsers.add_parser('list', help=usage.list_use)
    parser_list.add_argument('list_arg', #metavar="arg", 
                                action="store_true", help=usage.list_sub_use)

    # nargs options:
    # = N   where N is some specified number of args
    # = '?' makes a string of one item, and if no args are given, then default is used.
    # = '*' makes a list of all args passed after command and if no args given, then default is used.
    # = '+' makes list of all args passed after command, but requires at least one arg

    ### install command
    parser_install = subparsers.add_parser('install', help=usage.install_use.format(packages_file),
                                            formatter_class=argparse.RawTextHelpFormatter)
    parser_install.add_argument('install_arg', nargs='*', default=packages_file_path, #metavar="arg",  
                                help=usage.install_sub_use.format(packages_file))
    # parser_install.set_defaults(func=run_install)
    # then above would define:
    # def run_install(args):
    #   install_arg = args.install_arg  # would be a list of pkgs or a string of the packages file
    #   ...process the install_arg to decide what to install
    #   ...then do the install 


    ### remove command
    parser_remove = subparsers.add_parser('remove', help=usage.remove_use, 
                                            formatter_class=argparse.RawTextHelpFormatter)
    parser_remove.add_argument('remove_arg', nargs=1, 
                                help=usage.remove_sub_use)

    ### update command
    parser_update = subparsers.add_parser('update', help=usage.update_use,
                                            formatter_class=argparse.RawTextHelpFormatter)
    parser_update.add_argument('update_arg', nargs=1, 
                                help=usage.update_sub_use)


    ### turn_off command
    parser_turn_off = subparsers.add_parser('turn_off', help=usage.turn_off_use, 
                                            formatter_class=argparse.RawTextHelpFormatter)
    parser_turn_off.add_argument('turn_off_arg', nargs=1, 
                                help=usage.turn_off_sub_use)


    ### turn_on command
    parser_turn_on = subparsers.add_parser('turn_on', help=usage.turn_on_use, 
                                            formatter_class=argparse.RawTextHelpFormatter)
    parser_turn_on.add_argument('turn_on_arg', nargs=1, help=usage.turn_on_sub_use)#, metavar='arg')


    args = parser.parse_args()
    #print(args)
    #print(args.install_arg)
    #if 'install_arg' in args:
        #print(args.install_arg)

    # this turns args into a dict
    #args = vars(args)
    #print(args)
    #if 'install_arg' in args.keys():
        #print("yup")
    #parser.exit()

    ##########################################################
    ###########  this section handles cmds passed  ###########

    #def parse_command_args(cmd, cmdline_arg):
        #pkg_type_with_pkg_to_process = []   # this will be a list of tuples 
        #for pkg_type_and_pkg_to_process in cmdline_arg:
            #pkg_type_andor_pkg_to_process = pkg_type_and_pkg_to_process.split('=') 
            #if len(pkg_type_andor_pkg_to_process) != 2:
                #print("\nError: with argument {}.".format(pkg_type_andor_pkg_to_process[0]))
                #print("{} argument needs to be specified like so:".format(cmd))
                #print("\t`pkg_type=repo_type+pkg_name[^branch_name]`")
                #print("\t(eg. `{0} {1} github=git+ipython/ipython[^optional_branch]`)\n".format(name, cmd))
                #continue
                #raise SystemExit
            #pkg_type, pkg_to_process = pkg_type_andor_pkg_to_process
            #pkg_type_with_pkg_to_process.append((pkg_type, pkg_to_process))
        #return pkg_type_with_pkg_to_process #[(pkg_type, pkg_to_process1), (pkg_type, pkg_to_process2), ...] 


    class noise(object):
        verbose = args.verbose
        quiet = args.quiet


    lang_arg = args.language


    all_error = "\nError: Did you mean to specifiy ALL instead?"

    if 'install_arg' in args:
        install_arg = args.install_arg 

        if install_arg == packages_file_path:
            if lang_arg:
                print("\nError: cannot use language arg when installing packages from {};".format(packages_file))
                print("language needs to be specified for each package individually when installing")
                print("with {}. For example, a listing in {} would look like:".format(packages_file)) 
                print('\t"language-->[repo_type+]package_name[^optional_branch]"')
                print('\t(eg. "python3.3-->git+ipython/ipython[^optional_branch]")')
                raise SystemExit 

        elif install_arg != packages_file_path:
            if not lang_arg:
                print("\nError: Need to specify a language for installation.".format(packages_file))
                raise SystemExit 


    elif 'update_arg' in args:
        update_arg = args.update_arg[0] # list of one item 

        if update_arg in ['all', 'All']:
            raise SystemExit(all_error)


    elif 'remove_arg' in args:
        remove_arg = args.remove_arg[0]
       
        if remove_arg in ['all', 'All']:
            raise SystemExit(all_error)


    elif 'turn_off_arg' in args:
        turn_off_arg = args.turn_off_arg[0]

        if turn_off_arg in ['all', 'All']:
            raise SystemExit(all_error)


    elif 'turn_on_arg' in args:
        turn_on_arg = args.turn_on_arg[0]

        
    ##########################################################
    ##########################################################



    #--------------------------------------------------------------------------------------------------------------
    # where stuff actually happens
    if noise.quiet:
        print('-'*60)

    everything_already_installed = utils.all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir)
    #print('\neverything_already_installed:') 
    #print(everything_already_installed) 

    # install pkg(s) 
    # maybe make it so that multiple versions of the same package can be listed in the pkg file;
    #   though how to handle that all of them should be turned off except for one?

    if 'install_arg' in args:

        # install from packages file (the default)
        if install_arg == packages_file_path:   
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


            for pkg_type, pkgs_from_pkgs_file in pkgs_module.packages.items():
                utils.when_not_quiet_mode(utils.status('\t\tInstalling {0} packages'.format(pkg_type)), noise.quiet)

                if len(pkgs_from_pkgs_file) >= 1:

                    for pkg_to_install in pkgs_from_pkgs_file: 

                        lang_and_pkg_to_install = pkg_to_install.split('-->')  # to see if a language is given 
                        if len(lang_and_pkg_to_install) == 2:
                            lang_arg, pkg_to_install = lang_and_pkg_to_install
                            pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs, packages_file)
                        elif len(lang_and_pkg_to_install) != 2:
                            print("\nError: need to specifiy a language in {0} for:".format(packages_file)) 
                            print("\t{}".format(pkg_to_install))
                            raise SystemExit


                        # important to see what has previously been installed, so as to not turn on a 2nd version of a package.
                        everything_already_installed = utils.all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir) 
                        pkg_inst.install(pkg_to_install, noise, 
                                            everything_already_installed=everything_already_installed)
                else:
                    utils.when_not_quiet_mode('\nNo {0} packages specified in {1} to install.'.format(pkg_type, packages_file), noise.quiet)

        # install w/ command line arg(s)
        elif install_arg != packages_file_path:  

            pkg_type_with_pkg_to_process = []   # this will be a list of tuples 
            for pkg_type_and_pkg_to_process in install_arg:
                pkg_type_andor_pkg_to_process = pkg_type_and_pkg_to_process.split('=') # need this check b/c pkg_type has to be specified when using cmdline 
                if len(pkg_type_andor_pkg_to_process) != 2:
                    utils.how_to_specify_installation(pkg_type_andor_pkg_to_process[0])
                    #continue
                    raise SystemExit
                pkg_type, pkg_to_process = pkg_type_andor_pkg_to_process
                pkg_type_with_pkg_to_process.append((pkg_type, pkg_to_process))


            for pkg_type, pkg_to_install in pkg_type_with_pkg_to_process:


                pkg_to_install_specified_with_user_and_repo = pkg_to_install.split('/')
                if len(pkg_to_install_specified_with_user_and_repo) == 1:
                    if pkg_type != 'stable': 
                        print("\nError: need to specifiy a user and branch for {}, like:".format(pkg_to_install))
                        print("\t{} install github=git+username/pkg_name[^optional_branch]".format(name))   
                        raise SystemExit

                utils.when_not_quiet_mode(utils.status('\t\tInstalling {0} package'.format(pkg_type)), noise.quiet)
                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)

                # important to keep this here so it can be known what has previously been installed, so as to not turn on a 2nd version of a package.
                everything_already_installed = utils.all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir) 
                pkg_inst.install(pkg_to_install, noise, 
                                    everything_already_installed=everything_already_installed)

    


    # list installed pkg(s) (by each package type)
    elif 'list_arg' in args:
        if everything_already_installed:

            count_of_listed = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():

                if not lang_arg:  # if a language arg is not given, then list all installed packages
                    utils.when_not_quiet_mode("\n{0} packages installed:".format(lang_dir_name), noise.quiet)

                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    #if not lang_arg:  # if a language arg is given, then remove all pkgs for that lang's version
                        #when_not_quiet_mode("\t{0}:".format(pkg_type), noise.quiet)

                    if len(pkgs_and_branches) >= 1:

                        def list_packages(count_of_listed=count_of_listed):
                            for pkg_for_listing, branches in pkgs_and_branches.items(): 
                                for branch in branches:
                                    if branch.startswith('.__'):
                                        branch_if_were_on = branch.lstrip('.__')
                                        branch_if_were_on = '[{0}]'.format(branch_if_were_on)
                                        item_installed = '  {: >20} {: >25} {: >25} {: >10}'.format(pkg_for_listing, branch_if_were_on, pkg_type, "** off")

                                    elif not branch.startswith('.__'):                    
                                        branch = '[{0}]'.format(branch)
                                        item_installed = '  {: >20} {: >25} {: >25}'.format(pkg_for_listing, branch, pkg_type)
                                    count_of_listed += 1
                                    print(item_installed)
                            return count_of_listed

                        if lang_arg:  # if a language arg is given, then list pkgs for only that lang
                            pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                            lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                            if lang_dir_name == lang_cmd:
                                count_of_listed = list_packages()
                        else:
                            count_of_listed = list_packages()

            if count_of_listed == 0: 
                utils.when_not_quiet_mode('\n[ No packages for listing ]'.format(pkg_type), noise.quiet) 
        else:
            print('\nNo packages installed.') 



    # update pkg(s)
    elif 'update_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_updated = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = utils.pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                        pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                        pkgs_and_branches_off = pkgs_status['pkg_branches_off']

                        if update_arg == 'ALL':
                            if lang_arg:  # if a language arg is given, then update all pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    utils.when_not_quiet_mode(utils.status('\t\tUpdating {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                    count_of_pkgs_updated = 0
                                    for pkg_to_update, branch_on in pkgs_and_branches_on.items():
                                        for branch_to_update in branch_on:
                                            pkg_inst.update(lang_dir_name, pkg_to_update, branch_to_update, noise)
                                            count_of_pkgs_updated += 1
                                            top_count_of_pkgs_updated += 1

                                    if count_of_pkgs_updated == 0:
                                        utils.when_not_quiet_mode('\nNo {0} {1} packages turned on for updating.'.format(lang_dir_name, pkg_type), noise.quiet) 
                                        top_count_of_pkgs_updated = -1

                            else:  # if no language arg is given, then just update all installed pkgs
                                utils.when_not_quiet_mode(utils.status('\t\tUpdating {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type, install_dirs)

                                count_of_pkgs_updated = 0
                                for pkg_to_update, branch_on in pkgs_and_branches_on.items():
                                    for branch_to_update in branch_on:
                                        pkg_inst.update(lang_dir_name, pkg_to_update, branch_to_update, noise)
                                        count_of_pkgs_updated += 1
                                        top_count_of_pkgs_updated += 1

                                if count_of_pkgs_updated == 0:
                                    utils.when_not_quiet_mode('\nNo {0} {1} packages turned on for updating.'.format(lang_dir_name, pkg_type), noise.quiet) 
                                    top_count_of_pkgs_updated = -1



                        else: # for a single command passed to update
                            # a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's updated.

                            def how_to_update_branches(pkg_to_update, all_installed_for_pkg):
                                how_to_count = 0
                                for quad_tuple in all_installed_for_pkg: 
                                    lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
                                    if lang_installed == lang_dir_name: 
                                        if pkg_type_installed == pkg_type: 
                                            if not branch_installed.startswith('.__'): 
                                                if branch_installed == 'master':
                                                    print("\n* Update {0} {1} with:".format(pkg_to_update, lang_installed))
                                                    print("{0} -l {1} update {2}={3}".format(name, lang_installed, 
                                                                            pkg_type_installed, pkg_name_installed))
                                                else:
                                                    print("\n* Update {0} [{1}] {2} with:".format(pkg_to_update, branch_installed, 
                                                                                                    lang_installed))
                                                    print("{0} -l {1} update {2}={3}^{4}".format(name, lang_installed,
                                                                            pkg_type_installed, pkg_name_installed, branch_installed))

                                            elif branch_installed.startswith('.__'): 
                                                branch_installed = branch_installed.lstrip('.__')
                                                print("\n* {0} [{1}] {2} turned off:  turn on to update.".format(
                                                                                    pkg_name_installed, branch_installed, lang_installed))
                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def update_branch(pkg_to_update, branch_to_update, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
                                if lang_dir_name == lang_cmd:
                                    for pkg_name, branch_on in pkgs_and_branches_on.items():
                                        if pkg_name == pkg_to_update: 
                                            if branch_to_update in branch_on: 
                                                utils.when_not_quiet_mode(utils.status('\tUpdating {0} [{1}] {2} {3}'.format(
                                                        pkg_to_update, branch_to_update, lang_dir_name, pkg_type)), noise.quiet)
                                                pkg_inst.update(lang_cmd, pkg_to_update, branch_to_update, noise)
                                                was_pkg_processed = True

                                    for pkg_name, branches_off in pkgs_and_branches_off.items():
                                        if pkg_name == pkg_to_update: 
                                            if branch_to_update in branches_off: 
                                                branch_installed = branch_to_update.lstrip('.__')
                                                print("\n{0} [{1}] {2} turned off:  turn on to update.".format(
                                                                                    pkg_name, branch_installed, lang_cmd))
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_updated = utils.package_processor(lang_arg,
                                                                pkg_type,
                                                                pkg_info_raw=update_arg, 
                                                                how_to_func=how_to_update_branches,
                                                                processing_func=update_branch,
                                                                process_strs=dict(process='updating', action='update'),
                                                                everything_already_installed=everything_already_installed,
                                                                was_pkg_processed=False)       
                            if was_pkg_updated:
                                top_count_of_pkgs_updated += 1

            if top_count_of_pkgs_updated == 0: 
                utils.when_not_quiet_mode('\n[ No packages specified for updating ]'.format(pkg_type), noise.quiet) 
        else:
            print('\nNo packages installed.') 



    # remove pkg(s) 
    elif 'remove_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_removed = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = utils.pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                        pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                        pkgs_and_branches_off = pkgs_status['pkg_branches_off']


                        def remove_turned_off_branches(top_count_of_pkgs_removed, count_of_pkgs_removed=0):
                            for pkg_to_remove, branches_off in pkgs_and_branches_off.items():
                                for branch_to_remove in branches_off:
                                    branch_to_remove = '.__{0}'.format(branch_to_remove)
                                    pkg_inst.remove(pkg_to_remove, branch_to_remove, noise)
                                    count_of_pkgs_removed += 1; top_count_of_pkgs_removed += 1
                            return count_of_pkgs_removed

                        def remove_turned_on_branches(top_count_of_pkgs_removed, count_of_pkgs_removed=0):
                            for pkg_to_remove, branch_on in pkgs_and_branches_on.items():
                                for branch_to_remove in branch_on:
                                    pkg_inst.remove(pkg_to_remove, branch_to_remove, noise)
                                    count_of_pkgs_removed += 1; top_count_of_pkgs_removed += 1
                            return count_of_pkgs_removed


                        if remove_arg == 'ALL':
                            if lang_arg:  # if a language arg is given, then remove all pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    utils.when_not_quiet_mode(utils.status('\t\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                    count_of_turned_on_removed = remove_turned_on_branches(top_count_of_pkgs_removed)
                                    count_of_turned_off_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                    if (count_of_turned_on_removed or count_of_turned_off_removed):
                                        top_count_of_pkgs_removed = -1


                            else:  # if no language arg is given, then remove all installed pkgs
                                utils.when_not_quiet_mode(utils.status('\t\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type, install_dirs)
                                count_of_turned_on_removed = remove_turned_on_branches(top_count_of_pkgs_removed)
                                count_of_turned_off_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                if (count_of_turned_on_removed or count_of_turned_off_removed):
                                    top_count_of_pkgs_removed = -1


                        elif remove_arg == 'turned_off':
                            if lang_arg:  # if a language arg is given, then remove all turned off pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    utils.when_not_quiet_mode(utils.status('\tRemoving turned off {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                    count_of_pkgs_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                    if count_of_pkgs_removed == 0:
                                        utils.when_not_quiet_mode('\nNo {0} {1} packages turned off for removal.'.format(lang_dir_name, pkg_type), noise.quiet) 
                                        top_count_of_pkgs_removed = -1

                            else:  # if no language arg is given, then remove all turned off pkgs
                                utils.when_not_quiet_mode(utils.status('\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type, install_dirs)
                                count_of_pkgs_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                if count_of_pkgs_removed == 0:
                                    utils.when_not_quiet_mode('\nNo {0} {1} packages turned off for removal.'.format(lang_dir_name, pkg_type), noise.quiet) 
                                    top_count_of_pkgs_removed = -1



                        else: # for a single command passed to remove
                            # a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's removed

                            def how_to_remove_branches(pkg_to_remove, all_installed_for_pkg):
                                how_to_count = 0
                                for quad_tuple in all_installed_for_pkg: 
                                    lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
                                    if lang_installed == lang_dir_name: 
                                        if pkg_type_installed == pkg_type: 
                                            if branch_installed.startswith('.__'): 
                                                branch_installed = branch_installed.lstrip('.__')
                                            if branch_installed == 'master':
                                                print("\n* Remove {0} {1} with:".format(pkg_to_remove, lang_installed))
                                                print("{0} -l {1} remove {2}={3}".format(name, lang_installed, 
                                                                        pkg_type_installed, pkg_name_installed))
                                            else:
                                                print("\n* Remove {0} [{1}] {2} with:".format(pkg_to_remove, branch_installed, 
                                                                                                lang_installed))
                                                print("{0} -l {1} remove {2}={3}^{4}".format(name, lang_installed,
                                                                        pkg_type_installed, pkg_name_installed, branch_installed))

                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def remove_branch(pkg_to_remove, branch_to_remove, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
                                if lang_dir_name == lang_cmd:
                                    for pkg_name, branch_on in pkgs_and_branches_on.items():
                                        if pkg_name == pkg_to_remove: 
                                            if branch_to_remove in branch_on: 
                                                utils.when_not_quiet_mode(utils.status('\tRemoving {0} [{1}] {2} {3}'.format(
                                                        pkg_to_remove, branch_to_remove, lang_dir_name, pkg_type)), noise.quiet)
                                                pkg_inst.remove(pkg_to_remove, branch_to_remove, noise)
                                                was_pkg_processed = True

                                    for pkg_name, branches_off in pkgs_and_branches_off.items():
                                        if pkg_name == pkg_to_remove: 
                                            if branch_to_remove in branches_off: 
                                                utils.when_not_quiet_mode(utils.status('\tRemoving {0} [{1}] {2} {3}'.format(
                                                        pkg_to_remove, branch_to_remove, lang_dir_name, pkg_type)), noise.quiet)
                                                branch_to_remove = '.__{0}'.format(branch_to_remove)
                                                pkg_inst.remove(pkg_to_remove, branch_to_remove, noise)
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_removed = utils.package_processor(lang_arg,
                                                                pkg_type,
                                                                pkg_info_raw=remove_arg, 
                                                                how_to_func=how_to_remove_branches,
                                                                processing_func=remove_branch,
                                                                process_strs=dict(process='removal', action='remove'),
                                                                everything_already_installed=everything_already_installed,
                                                                was_pkg_processed=False)       
                            if was_pkg_removed:
                                top_count_of_pkgs_removed += 1

            if top_count_of_pkgs_removed == 0: 
                utils.when_not_quiet_mode('\n[ No packages specified for removing ]'.format(pkg_type), noise.quiet) 
        else:
            print('\nNo packages installed.') 




    # turn off pkg(s) 
    elif 'turn_off_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_turned_off = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = utils.pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                        pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                        pkgs_and_branches_off = pkgs_status['pkg_branches_off']


                        def turn_off_branches(top_count_of_pkgs_turned_off, count_of_pkgs_turned_off=0):
                            for pkg_to_turn_off, branch_on in pkgs_and_branches_on.items():
                                for branch_to_turn_off in branch_on:
                                    pkg_inst.turn_off(pkg_to_turn_off, branch_to_turn_off, noise)
                                    count_of_pkgs_turned_off += 1; top_count_of_pkgs_turned_off += 1
                            return count_of_pkgs_turned_off


                        if turn_off_arg == 'ALL':
                            if lang_arg:  # if a language arg is given, then turn off all pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    utils.when_not_quiet_mode(utils.status('\t\tTurning off {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                    count_of_turned_off = turn_off_branches(top_count_of_pkgs_turned_off)
                                    if count_of_turned_off:
                                        top_count_of_pkgs_turned_off = -1

                            else:  # if no language arg is given, then turn off all installed pkgs
                                utils.when_not_quiet_mode(utils.status('\t\tTurning off {0} {1} packages'.format(lang_dir_name, pkg_type)), noise.quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type, install_dirs)
                                count_of_turned_off = turn_off_branches(top_count_of_pkgs_turned_off)
                                if count_of_turned_off:
                                    top_count_of_pkgs_turned_off = -1

                        else: # for a single command passed to turn off
                            # a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's turned off

                            def how_to_turn_off_branches(pkg_to_turn_off, all_installed_for_pkg):
                                how_to_count = 0
                                for quad_tuple in all_installed_for_pkg: 
                                    lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
                                    if lang_installed == lang_dir_name: 
                                        if pkg_type_installed == pkg_type: 

                                            if not branch_installed.startswith('.__'): 
                                                if branch_installed == 'master':
                                                    print("\n* Turn off {0} {1} with:".format(pkg_to_turn_off, lang_installed))
                                                    print("{0} -l {1} turn_off {2}={3}".format(name, lang_installed, 
                                                                            pkg_type_installed, pkg_name_installed))
                                                else:
                                                    print("\n* Turn off {0} [{1}] {2} with:".format(pkg_to_turn_off, branch_installed, 
                                                                                                    lang_installed))
                                                    print("{0} -l {1} turn_off {2}={3}^{4}".format(name, lang_installed,
                                                                            pkg_type_installed, pkg_name_installed, branch_installed))

                                            elif branch_installed.startswith('.__'): 
                                                branch_installed = branch_installed.lstrip('.__')
                                                print("\n* {0} [{1}] {2} already turned off.".format(pkg_name_installed, branch_installed, lang_installed))

                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def turn_off_branch(pkg_to_turn_off, branch_to_turn_off, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
                                if lang_dir_name == lang_cmd:
                                    for pkg_name, branch_on in pkgs_and_branches_on.items():
                                        if pkg_name == pkg_to_turn_off: 
                                            if branch_to_turn_off in branch_on: 
                                                utils.when_not_quiet_mode(utils.status('\tTurning off {0} [{1}] {2} {3}'.format(
                                                        pkg_to_turn_off, branch_to_turn_off, lang_dir_name, pkg_type)), noise.quiet)
                                                pkg_inst.turn_off(pkg_to_turn_off, branch_to_turn_off, noise)
                                                was_pkg_processed = True

                                    for pkg_name, branches_off in pkgs_and_branches_off.items():
                                        if pkg_name == pkg_to_turn_off: 
                                            if branch_to_turn_off in branches_off: 
                                                #branch_installed = branch_to_turn_off.lstrip('.__')
                                                print('\n{0} [{1}] {2} already turned off.'.format(pkg_to_turn_off, branch_to_turn_off, lang_cmd)) 
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_turned_off = utils.package_processor(lang_arg,
                                                                pkg_type,
                                                                pkg_info_raw=turn_off_arg, 
                                                                how_to_func=how_to_turn_off_branches,
                                                                processing_func=turn_off_branch,
                                                                process_strs=dict(process='turning off', action='turn_off'),
                                                                everything_already_installed=everything_already_installed,
                                                                was_pkg_processed=False)       
                            if was_pkg_turned_off:
                                top_count_of_pkgs_turned_off += 1

            if top_count_of_pkgs_turned_off == 0: 
                utils.when_not_quiet_mode('\n[ No packages specified for turning off ]'.format(pkg_type), noise.quiet) 
        else:
            print('\nNo packages installed.') 


    # turn on pkg(s) 
    elif 'turn_on_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_turned_on = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = utils.pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                        pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                        pkgs_and_branches_off = pkgs_status['pkg_branches_off']

                        if turn_on_arg: # for a single command passed to turn on
                            # a specific branch of a specific pkg of a specific pkg_type for a specific lang is what's turned on

                            def how_to_turn_on_branches(pkg_to_turn_on, all_installed_for_pkg):
                                how_to_count = 0
                                for quad_tuple in all_installed_for_pkg: 
                                    lang_installed, pkg_type_installed, pkg_name_installed, branch_installed = quad_tuple
                                    if lang_installed == lang_dir_name: 
                                        if pkg_type_installed == pkg_type: 

                                            if branch_installed.startswith('.__'): 
                                                branch_installed = branch_installed.lstrip('.__')
                                                if branch_installed == 'master':
                                                    print("\n* Turn on {0} {1} with:".format(pkg_to_turn_on, lang_installed))
                                                    print("{0} -l {1} turn_on {2}={3}".format(name, lang_installed, 
                                                                            pkg_type_installed, pkg_name_installed))
                                                else:
                                                    print("\n* Turn on {0} [{1}] {2} with:".format(pkg_to_turn_on, branch_installed, 
                                                                                                    lang_installed))
                                                    print("{0} -l {1} turn_on {2}={3}^{4}".format(name, lang_installed,
                                                                            pkg_type_installed, pkg_name_installed, branch_installed))

                                            elif not branch_installed.startswith('.__'): 
                                                print("\n* {0} [{1}] {2} already turned on.".format(pkg_name_installed, branch_installed, lang_installed))
                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def turn_on_branch(pkg_to_turn_on, branch_to_turn_on, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type, install_dirs)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
                                if lang_dir_name == lang_cmd:
                                    for pkg_name, branch_on in pkgs_and_branches_on.items():
                                        if pkg_name == pkg_to_turn_on: 
                                            if branch_to_turn_on in branch_on: 
                                                print('\n{0} [{1}] {2} already turned on.'.format(pkg_to_turn_on, branch_to_turn_on, lang_cmd)) 
                                                was_pkg_processed = True

                                    for pkg_name, branches_off in pkgs_and_branches_off.items():
                                        if pkg_name == pkg_to_turn_on: 
                                            if branch_to_turn_on in branches_off: 
                                                utils.when_not_quiet_mode(utils.status('\tTurning on {0} [{1}] {2} {3}'.format(
                                                        pkg_to_turn_on, branch_to_turn_on, lang_dir_name, pkg_type)), noise.quiet)
                                                branch_to_turn_on = '.__{0}'.format(branch_to_turn_on)
                                                pkg_inst.turn_on(pkg_to_turn_on, branch_to_turn_on, everything_already_installed, noise)
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_turned_on = utils.package_processor(lang_arg,
                                                                pkg_type,
                                                                pkg_info_raw=turn_on_arg, 
                                                                how_to_func=how_to_turn_on_branches,
                                                                processing_func=turn_on_branch,
                                                                process_strs=dict(process='turning on', action='turn_on'),
                                                                everything_already_installed=everything_already_installed,
                                                                was_pkg_processed=False)       
                            if was_pkg_turned_on:
                                top_count_of_pkgs_turned_on += 1

            if top_count_of_pkgs_turned_on == 0: 
                utils.when_not_quiet_mode('\n[ No packages specified for turning on ]'.format(pkg_type), noise.quiet) 
        else:
            print('\nNo packages installed.') 
