#! /usr/bin/env python

"""
#----------------------------------------------------------------
Author: Jason Gors <jasonDOTgorsATgmail>
Creation Date: 07-30-2013
Purpose: this manages provides utility functions for managing 
            the packages.  
#----------------------------------------------------------------
"""

from Bep.core.release_info import name
import os
from os.path import join
import glob



def all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir):
    ''' builds up info on all pkgs and branches installed for all pkg_types for a 
        specific version of the install lang. '''

    all_pkgs_and_branches_for_all_pkg_types_already_installed = {}
    
    langs_paths = glob.glob(join(installed_pkgs_dir, '*'))

    for lang_path in langs_paths: 
        lang_name = os.path.basename(lang_path)
        all_pkgs_and_branches_for_all_pkg_types_already_installed.update({ lang_name: {} })
        pkg_types_paths = glob.glob(join(lang_path, '*'))

        for pkg_type_path in pkg_types_paths:
            pkg_type_name = os.path.basename(pkg_type_path)
            all_pkgs_and_branches_for_all_pkg_types_already_installed[lang_name].update({ pkg_type_name: {} })
            pkg_names_paths = glob.glob(join(pkg_type_path, '*'))

            for pkg_name_path in pkg_names_paths: 
                pkg_name = os.path.basename(pkg_name_path)
                all_pkgs_and_branches_for_all_pkg_types_already_installed[lang_name][pkg_type_name].update({ pkg_name: [] })
                branches_paths = glob.glob(join(pkg_name_path, '*')) + glob.glob(join(pkg_name_path, '.*')) # b/c glob ignores hidden stuff
            
                for branch_path in branches_paths:
                    branch_name = os.path.basename(branch_path)
                    all_pkgs_and_branches_for_all_pkg_types_already_installed[lang_name][pkg_type_name][pkg_name].append(branch_name)

    return all_pkgs_and_branches_for_all_pkg_types_already_installed


def pkgs_and_branches_for_pkg_type_status(pkgs_and_branches_installed_for_pkg_type_lang):
    ''' tells whether branches for the packages are turned on/off '''

    all_pkg_branches_with_hidden_raw = {}
    all_pkg_branches_with_hidden_renamed = {}
    pkg_branches_on = {} # there will be only one on at a time for each pkg_installed
    pkg_branches_off = {}

    for pkg_installed, branches in pkgs_and_branches_installed_for_pkg_type_lang.items(): 

        all_pkg_branches_with_hidden_raw.update({pkg_installed: []})
        all_pkg_branches_with_hidden_renamed.update({pkg_installed: []})
        pkg_branches_on.update({pkg_installed: []})
        pkg_branches_off.update({pkg_installed: []})

        for branch in branches:
            all_pkg_branches_with_hidden_raw[ pkg_installed ].append(branch)          
            if not branch.startswith('.__'):    # branch is on
                pkg_branches_on[ pkg_installed ].append(branch)          
                all_pkg_branches_with_hidden_renamed[ pkg_installed ].append(branch)          

            elif branch.startswith('.__'):      # branch is off
                branch_off = branch.lstrip('.__')
                pkg_branches_off[ pkg_installed ].append(branch_off)          
                all_pkg_branches_with_hidden_renamed[ pkg_installed ].append(branch_off)          

    pkg_branches = dict(all_pkg_branches_with_hidden_raw = all_pkg_branches_with_hidden_raw,
                        all_pkg_branches_with_hidden_renamed = all_pkg_branches_with_hidden_renamed,
                        pkg_branches_on = pkg_branches_on,
                        pkg_branches_off = pkg_branches_off) 
        # { all_pkg_branches_with_hidden_raw:   {pkg_name1: [branches_on_&_off, ...], pkg_name2: [branches_on_&_off, ...]},
        #   all_pkg_branches_with_hidden_renamed:   {pkg_name1: [branches_on_&_off, ...], pkg_name2: [branches_on_&_off, ...]},
        #   pkg_branches_on:    {pkg_name1: [branch_on], pkg_name2: [branch_on]},
        #   pkg_branches_off:   {pkg_name1: [branch(es)_off, ...], pkg_name2: [branch(es)_off, ...]} }
    return pkg_branches 


# pkg_and_branches_all = pkgs_and_branches_for_pkg_type_status['all_pkg_branches_with_hidden_renamed'] 
# branches_installed_for_pkg =  pkg_and_branches_all[ pkg_name ] 
# eg. pkg_and_branches_all['ipython'] -- to get all the branches installed (on & off's renamed) for this pkg

#everything_installed = all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir) 
#for pkg_type in everything_installed:
    #print(pkg_type)
    #pkg_name_and_branches = pkgs_and_branches_for_pkg_type(pkg_type)
    ##print('\t', pkg_name_and_branches)
    ##print()
    #print('\t', pkgs_and_branches_for_pkg_type_status(pkg_name_and_branches)) 
    #print() 


def branches_installed_for_given_pkgs_lang_ver(lang_cmd, pkg_to_process_name, everything_already_installed):
    ''' returns a list of all branches that are installed for a specific pkg, 
        for a specific version of the lang across all pkg types '''
    all_branches_installed_for_pkgs_lang_ver = [] 

    for lang_installed, pkg_types_dict in everything_already_installed.items():
        if lang_installed == lang_cmd:
            for pkg_type, pkgs_dict in pkg_types_dict.items():
                for installed_pkg_name, branches_list in pkgs_dict.items(): 
                    if pkg_to_process_name == installed_pkg_name: 
                        for branch in branches_list:
                            all_branches_installed_for_pkgs_lang_ver.append(branch)

    return all_branches_installed_for_pkgs_lang_ver


def lang_and_pkg_type_and_pkg_and_branches_tuple(pkg_process, everything_already_installed):
    ''' gives back a tuple with all installed versions of a package, for different pkg_types and
        for different branches '''
    lang_pkg_type_pkg_and_branches_for_lang = [] 

    for lang_installed, pkg_types_dict in everything_already_installed.items():
        for installed_pkg_type, pkg_and_branches_dict in pkg_types_dict.items():
            for installed_pkg_name, branches_list in pkg_and_branches_dict.items(): 
                if pkg_process == installed_pkg_name: 
                    for branch in branches_list:
                        lang_pkg_type_pkg_and_branches_for_lang.append(
                                (lang_installed, installed_pkg_type, installed_pkg_name, branch))

    #[(lang, pkg_type, pkg_1, branch), (lang, pkg_type, pkg_1, branch), ...]  
    return lang_pkg_type_pkg_and_branches_for_lang 


def package_processor(lang_arg, pkg_type, pkg_info_raw, how_to_func, processing_func, 
                            process_strs, everything_already_installed, was_pkg_processed): 
    ''' this is used by command line arg passed to the script to decide 
        whether to proceed with the command '''

    # everything possible via pkg_info_raw:   "pkg_type = repo_type + pkg_name ^ branch"
    pkg_type_n_repo_type_n_pkg_name_n_branch_to_process = pkg_info_raw.split('=') 
    # ["pkg_type",   "repo_type + pkg_name ^ branch"]

    if len(pkg_type_n_repo_type_n_pkg_name_n_branch_to_process) == 1:  # would mean pkg_type was not given 

        repo_type_n_pkg_name_n_branch_to_process = pkg_type_n_repo_type_n_pkg_name_n_branch_to_process[-1]
        # ["repo_type + pkg_name ^ branch"]

        repo_type_n_pkg_name_n_branch_to_process = repo_type_n_pkg_name_n_branch_to_process.split('+')
        # ["repo_type",   "pkg_name ^ branch"] 

        pkg_name_n_branch_to_process = repo_type_n_pkg_name_n_branch_to_process[-1]
        # ["pkg_name ^ branch"] 

        pkg_name_n_branch_to_process = pkg_name_n_branch_to_process.split('^')
        # ["pkg_name",   "branch"] 

        pkg_name_to_process = pkg_name_n_branch_to_process[0]
        # ["pkg_name"] 

        all_installed_for_pkg = lang_and_pkg_type_and_pkg_and_branches_tuple(
                                            pkg_name_to_process, everything_already_installed)
        #print('all_installed_for_pkg:')
        #print(all_installed_for_pkg) 
        if all_installed_for_pkg: # if there are any branches for the package name passed in
            any_pkg_how_to_suggested = how_to_func(pkg_name_to_process, all_installed_for_pkg)
            return any_pkg_how_to_suggested  # either 0 or -1

    
    elif len(pkg_type_n_repo_type_n_pkg_name_n_branch_to_process) == 2:  # would mean pkg_type was given 

        if lang_arg:

            pkg_type_to_process, repo_type_n_pkg_name_n_branch_to_process = pkg_type_n_repo_type_n_pkg_name_n_branch_to_process
            # "pkg_type",   ["repo_type + pkg_name ^ branch"]

            repo_type_n_pkg_name_n_branch_to_process = repo_type_n_pkg_name_n_branch_to_process.split('+')
            # ["repo_type",   "pkg_name ^ branch"] 

            pkg_name_n_branch_to_process = repo_type_n_pkg_name_n_branch_to_process[-1]  # b/c don't care about repo_type (it's only needed for installs)
            # ["pkg_name ^ branch"] 

            pkg_name_n_branch_to_process = pkg_name_n_branch_to_process.split('^')
            # ["pkg_name",   "branch"] 
            
            if len(pkg_name_n_branch_to_process) == 1:
                pkg_to_process = pkg_name_n_branch_to_process[0]
                # "pkg_name" 

                pkg_to_process = os.path.basename(pkg_to_process) 
                branch_to_process = 'master'

                if pkg_type_to_process == pkg_type: 
                    was_pkg_processed = processing_func(pkg_to_process, branch_to_process, was_pkg_processed)
                    return was_pkg_processed # either True or False

            elif len(pkg_name_n_branch_to_process) == 2:
                pkg_to_process, branch_to_process = pkg_name_n_branch_to_process 

                # change the name of a repo branch that is specified with a nested path (a '/') in order to 
                # make nested branch names be flattened (with a '_' instead)
                branch_to_process = branch_to_process.split('/')   
                if len(branch_to_process) == 1:
                    branch_to_process = branch_to_process[0]
                elif len(branch_to_process) >= 1:
                    branch_to_process = '_'.join(branch_to_process)

                pkg_to_process = os.path.basename(pkg_to_process) # in case pkg_to_process is given like ipython/ipython 

                if pkg_type_to_process == pkg_type: 
                    was_pkg_processed = processing_func(pkg_to_process, branch_to_process, was_pkg_processed)
                    return was_pkg_processed # either True or False
        else:
            print("\nError: To specify a package for {process}, need to specify language arg.".format(**process_strs)) 
            raise SystemExit

    else:
        print("\nError: To specify a package for {process}, see results of:".format(**process_strs)) 
        print("  {} {action} pkg_name".format(name, **process_strs))
        raise SystemExit

    return was_pkg_processed



status = lambda x: "\n\n{0}\n{1}\n{0}".format('-'*65, x)


def when_not_quiet_mode(output, be_quiet=False):
    if not be_quiet:
        print('{0}'.format(output))
    elif be_quiet:
        #print('\n')
        pass


def how_to_specify_installation(installation_arg):
    print("\nError: with argument {}.".format(installation_arg))
    print("install argument needs to be specified like so:")
    print("\t`pkg_type=repo_type+pkg_name[^branch_name]`")
    print("\t(eg. `{} install github=git+ipython/ipython[^optional_branch]`)\n".format(name))
