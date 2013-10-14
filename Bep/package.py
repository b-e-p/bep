#! /usr/bin/env python

"""
#----------------------------------------------------------------
Author: Jason Gors <jasonDOTgorsATgmail>
Creation Date: 07-30-2013
Purpose: this manages installation of packages -- currently: git repos from github &
        gitorious; git & hg repos from bitbucket; git, hg & bzr local repos.  
#----------------------------------------------------------------
"""

import os
from os.path import join
import shutil
import subprocess
import sys 
import glob
import itertools
import locale   # needed in py3 for decoding output from subprocess pipes 
import imp
import site
import Bep.languages as languages
import Bep.core.usage as usage 
from Bep.core.release_info import __version__, name
#from core.utils_db import (handle_db_after_an_install, handle_db_for_removal,
                        #handle_db_for_branch_renaming,
                        #get_lang_cmd_branch_was_installed_with)


class Package(object):
    def __init__(self, lang_arg, pkg_type):

        if 'python' in lang_arg:
            self.lang_using = languages.Python()
        #elif 'otherlanguage' in lang_arg:  # for other languages
            #self.lang_using = languages.OtherLanguage()
        else:
            print("\nError: {0} currently not supported.".format(lang_arg))
            raise SystemExit

        self.lang_cmd = self.lang_using.get_lang_cmd(lang_arg)

        self.pkg_type = pkg_type

        self.installed_pkgs_dir = installed_pkgs_dir
        self.install_logs_dir = install_logs_dir  

        self.lang_install_dir = join(installed_pkgs_dir, self.lang_cmd)
        self.lang_logs_dir = join(install_logs_dir, self.lang_cmd)

        self.pkg_type_install_dir = join(self.lang_install_dir, self.pkg_type) 
        self.pkg_type_logs_dir = join(self.lang_logs_dir, self.pkg_type) 


    def _cmd_output(self, cmd, verbose):
        encoding = locale.getdefaultlocale()[1]     # py3 stuff b/c this is encoded as b('...')
        if verbose:    # shows all the output when running cmd -- sometimes lots of stuff
            print(cmd)
            #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            #for line in p.stdout:
                #line = line.decode(encoding)
                #print(line.rstrip())
            #return_val = p.wait()

            cmd = cmd.split(' ') # to use w/o setting needing to set shell=True
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout:
                line = line.decode(encoding)
                print(line.rstrip())
            return_val = p.wait()

        else:   # for a quiet mode -- only shows the output when the cmd fails
            #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            #out, err = p.communicate()
            #self.out = out.decode(encoding) 
            #self.err = err.decode(encoding)
            #return_val = p.returncode

            cmd = cmd.split(' ') # to use w/o setting needing to set shell=True
            #print('cmd:'); print(cmd)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            self.out = out.decode(encoding) 
            self.err = err.decode(encoding)
            return_val = p.returncode

        return return_val


    def parse_pkg_to_install_name(self, pkg_to_install):

        def strip_end_of_str(str_to_strip):
            if str_to_strip.endswith('/'):
                return str_to_strip.rstrip('/')     # b/c noticed problem with local_repo installs
            elif str_to_strip.endswith('.git'):
                return str_to_strip.rstrip('.git')  # would be a problem if git repos have this at the end 
            else:
                return str_to_strip                 # if nothing wrong, then just give back the string feed into this here.

        # this bit looks to see if a branch is specified for installing; if not, then it gets master.
        pkg_branch_test = pkg_to_install.split('^')
        assert len(pkg_branch_test) <= 2, "Only allowed to specify one branch per package listing for installation."
        if len(pkg_branch_test) == 2:
            pkg_to_install, branch = pkg_branch_test
            pkg_to_install = strip_end_of_str(pkg_to_install) 

            if len(pkg_to_install.split('/')) == 1:
                how_to_specify_installation(pkg_to_install)
                raise SystemExit

            download_url = self.download_url.format(pkg_to_install)
            download_info = self.download_url_cmd.format(branch, download_url)
        elif len(pkg_branch_test) == 1:
            branch = 'master' 
            pkg_to_install = pkg_branch_test[0]
            pkg_to_install = strip_end_of_str(pkg_to_install) 
            download_info = self.download_url.format(pkg_to_install)

        # if repo branch name is specified with a nested path, then change its name (in order 
        # to install all branches flattened in the pkg_dir)
        branch = branch.split('/')   
        if len(branch) == 1:
            branch = branch[0]
        elif len(branch) >= 1:
            branch = '_'.join(branch)
                
        pkg_to_install_name = os.path.basename(pkg_to_install)
        self.install_download_cmd = self.install_download_cmd.format(download_info, branch)

        return pkg_to_install_name, branch 


    def _download_pkg(self, pkg_to_install_name, branch_to_install_name, verbose):
        ''' downloads/clones the specified package branch for installation '''

        # tests whether the vc application is installed ('git', 'hg', 'bzr', maybe others in the future )
        app_check_cmd = self.application_check_cmd
        app_type = app_check_cmd.split(' ')[0]
        return_val = self._cmd_output(app_check_cmd, verbose=False)
        if return_val:  # it would be zero if the program is installed (if anything other than zero, then it's not installed)
            print("\nError: COULD NOT INSTALL {0} packages; are you sure {1} is installed?".format(self.pkg_type, app_type))
            return None

        # make the initial pkg_name_dir 
        pkg_name_dir = join(self.pkg_type_install_dir, pkg_to_install_name)
        if not os.path.isdir(pkg_name_dir):
            os.makedirs(pkg_name_dir)

        when_not_quiet_mode('Downloading {0} [{1}]...'.format(pkg_to_install_name, branch_to_install_name), quiet)

        # download the branch to the pkg_name_dir 
        os.chdir(pkg_name_dir)
        return_val = self._cmd_output(self.install_download_cmd, verbose)

        if return_val != 0:
            print("Could not properly download {0} [{1}] with {2}\n".format(pkg_to_install_name, branch_to_install_name, self.repo_type)) 

            # remove whatever may have been downloaded that didn't get successfully downloaded
            something_downloaded_or_already_in_pkg_name_dir = glob.glob(pkg_name_dir)
            if not something_downloaded_or_already_in_pkg_name_dir:  # if nothing was downloaded
                shutil.rmtree(pkg_name_dir) # if the install didn't work, then remove the pkg_name_dir
                if not os.listdir(self.pkg_type_install_dir): # if the pkg type install dir is empty, remove that
                    os.rmdir(self.pkg_type_install_dir)
                if not os.listdir(self.lang_install_dir): # finally, if the lang install dir is empty, remove that
                    shutil.rmtree(self.lang_install_dir)
                
            # if the pkg_name_dir is not empty, then just remove the specific branch_to_install_name that was attempted to 
            # be downloaded, and leave everything else in there alone. 
            else:
                try:
                    shutil.rmtree(branch_to_install_name) # if the install didn't work, then remove the downloaded pkg dir
                # might need this b/c maybe it didn't even create the branch_to_install_name dir (eg. b/c of a wrongly 
                # specified command - git when hg should have been used)
                except: pass    
            return None

        elif return_val == 0:   # the download was sucessfull 
            return True


    def _installation_check(self, pkg_type, pkg_to_install_name, branch_to_install, everything_already_installed):
        '''
        to make sure that only one version of any given package can be turned on (/active) at any given 
        time for a specific version of the lang.  If a package branch with the same name as an already 
        installed (turned off) pkg branch is attempting to be installed under the same pkg_type, then do 
        not allow this; however, do allow it for a pkg branch with the same name as an existing package 
        branch, but under a diff pkg type.
        '''
        pkg_name = pkg_to_install_name
        branch_name = branch_to_install

        all_branches_installed_for_pkgs_lang_ver = branches_installed_for_given_pkgs_lang_ver(
                                                            self.lang_cmd, 
                                                            pkg_to_install_name, everything_already_installed) 

        # make a list of any branch that is currently turned on for this package, regardless of pkg type;
        # should only be one branch on at any given time!
        any_package_branch_on = [branch for branch in all_branches_installed_for_pkgs_lang_ver if not branch.startswith('.__')]
        
        # make a list of all branches (hidden renamed) currently installed for this package
        #all_branches_already_installed = [branch.lstrip('.__') if branch.startswith('.__') else branch for branch in all_branches_installed_for_pkg]

        #print('everything_already_installed:')
        #print(everything_already_installed)

        for lang_installed, pkg_types_dict in everything_already_installed.items():
            if lang_installed == self.lang_cmd:
                for installed_pkg_type, pkgs_dict in pkg_types_dict.items():
                    for installed_pkg_name, branches_list in pkgs_dict.items(): 

                        # make a list of any branch that is currently turned on for this pkg name via this package type;
                        # should only be one branch on at a time for the package name across all pkg types.
                        pkg_branch_names_on_for_pkg_type = [branch for branch in branches_list if not branch.startswith('.__')]

                        # make a list of any branch that is currently turned off for this pkg name via package type
                        pkg_branch_names_off_for_pkg_type = [branch.lstrip('.__') for branch in branches_list if branch.startswith('.__')]

                        pkg_branch_names_all_for_pkg_type = pkg_branch_names_on_for_pkg_type + pkg_branch_names_off_for_pkg_type 
                        

                        if any_package_branch_on:
                                #(ipy)       (ipy)
                            if pkg_name == installed_pkg_name:
                                    #(Github)    (Github)
                                if pkg_type == installed_pkg_type: 
                                    #(ipy_master)  (ipy_master)
                                    if branch_name in pkg_branch_names_on_for_pkg_type:
                                        print("Already installed & turned on.") 
                                        return False

                                        #(ipy_master) (.__ipy_master renamed to ipy_master)
                                    if branch_name in pkg_branch_names_off_for_pkg_type:
                                        print("Already installed & turned off.") 
                                        return False

                                    # these two statements below mean the same thing (i think); b/c if the branch is not
                                    # in the installed branches for this pkg & pkg_type, then the branch would have to 
                                    # be (turned on) in a different pkg_type (under the same pkg name of course).
                                        #(ipy_master)        (anything but ipy_master)
                                    if branch_name not in pkg_branch_names_all_for_pkg_type:
                                        print("A branch of {0} is already turned on for {1}.".format(pkg_name, lang_installed))
                                        return False # b/c there is already a branch on somewhere 

                                        #(ipy_master)   (in the list of any branch turned on for this pkg, regardless of pkg_type)
                                    if branch_name in any_package_branch_on:
                                        print("A branch of {0} is already turned on for {1}.".format(pkg_name, lang_installed))
                                        return False # b/c there is already a branch on somewhere 

                                    #(Github)     (Local Repo)
                                elif pkg_type != installed_pkg_type:

                                        #(ipy_master)   (ipy_master)
                                    if branch_name in pkg_branch_names_on_for_pkg_type:
                                        #print("A branch of {} is already turned on under {} packages.".format(pkg_name, installed_pkg_type))
                                        print("A branch of {0} is already turned on for {1}.".format(pkg_name, lang_installed))
                                        return False # b/c there is already a pkg branch turned on somewhere

                                        #(ipy_master)       (anything not ipy_master) 
                                    if branch_name not in pkg_branch_names_all_for_pkg_type:
                                        print("A branch of {0} is already turned on for {1}.".format(pkg_name, lang_installed))
                                        return False # b/c there is already a pkg branch turned on somewhere

                                    #if branch_name in any_package_branch_on:
                                        #print("A branch of {} is already turned on.".format(pkg_name))
                                        #return False # b/c there is already a branch on somewhere 

                            ### don't care about these tests
                                    ##(ipy)       (sklearn)
                            #elif pkg_name != installed_pkg_name:
                                    #(Github)    (Github)
                                #if pkg_type == installed_pkg_type:
                                        ##(master)       (master)
                                    #if branch_name in installed_branch_names_raw:
                                        #return False # b/c this doesn't matter 
                                        ##(master)           (anything not master) 
                                    #elif branch_name not in installed_branch_names_raw:
                                        #return False # # b/c this doesn't matter 

                                    ##(Github)     (Local Repo)
                                #elif pkg_type != installed_pkg_type:
                                        ##(master)       (master)
                                    #if branch_name in installed_branch_names_raw:
                                        #return False # b/c this doesn't matter
                                        ##(master)           (anything but master) 
                                    #elif branch_name not in installed_branch_names_raw:
                                        #return False # b/c this doesn't matter 

                        elif not any_package_branch_on: # if no branch is turned on for this package

                                #(ipy)       (ipy)
                            if pkg_name == installed_pkg_name:
                                #(Github)      (Github)
                                if pkg_type == installed_pkg_type:

                                        #(ipy_master)   (ipy_master renamed from .__ipy_master)
                                    if branch_name in pkg_branch_names_off_for_pkg_type:
                                        print("Already installed & turned off.")
                                        return False # b/c the branch is already installed for this pkg_name under this pkg_type but turned off.

                                        #(ipy_master)         (anything but ipy_master)
                                    elif branch_name not in pkg_branch_names_off_for_pkg_type:
                                        return True # b/c there are not any pkg branches turned on and this branch isn't already installed for this pkg_type 

                                    #(Github)     (Local Repo)
                                #elif pkg_type != installed_pkg_type:

                                        ##(ipy_master)  (ipy_master)
                                    #if branch_name in pkg_branch_names_off_for_pkg_type:
                                        # b/c it doesn't matter what branches are installed under a different pkg_type (so long as no branches are on)
                                        #return True  

                                        ##(ipy_master)        (anything but ipy_master)
                                    #elif branch_name not in pkg_branch_names_off_for_pkg_type:
                                        # b/c it doesn't matter what branches are installed under a different pkg_type (so long as no branches are on)
                                        #return True  


                            ### don't care about these tests
                                ##(ipy)        (sklearn)
                            #elif pkg_name != installed_pkg_name:
                                ##(Github)      (Github)
                                #if pkg_type == installed_pkg_type:
                                        ##(master)      (master)
                                    #if branch_name in installed_branch_names_renamed:
                                        #return False # b/c this doesn't matter
                                        ##(master)           (anything but master) 
                                    #elif branch_name not in installed_branch_names_renamed:
                                        #return False # b/c this doesn't matter 

                                    ##(Github)     (Local Repo)
                                #elif pkg_type != installed_pkg_type:
                                        ##(master)      (master)
                                    #if branch_name in installed_branch_names_renamed:
                                        #return False # b/c this doesn't matter 
                                        ##(master)        (anything but master)
                                    #elif branch_name not in installed_branch_names_renamed:
                                        #return False # b/c this doesn't matter 

        # True means that the branch can be installed b/c it wasn't caught in one of the false returns above.
        # Also, this returns True if there are no packages installed (like when using for the first time).                   
        return True 



    def install(self, pkg_to_install, verbose, download_pkg=True, everything_already_installed=None):
        ''' installs the specified package's branch ''' 

        def do_install(pkg_to_install_name, branch_to_install):

            pkg_install_dir = join(self.pkg_type_install_dir, pkg_to_install_name)
            pkg_logs_dir = join(self.pkg_type_logs_dir, pkg_to_install_name)

            branch_install_dir = join(pkg_install_dir, branch_to_install)
            branch_logs_dir = join(pkg_logs_dir, branch_to_install)

            # go into the branch install dir and try to install the branch 
            os.chdir(branch_install_dir)

            record_file = self.lang_using._create_record_log_file(self.pkg_type_logs_dir, pkg_to_install_name, branch_to_install)
            install_cmd = self.lang_using.get_install_cmd(pkg_to_install_name, branch_to_install, self.lang_cmd, record_file)

            contents_of_pkg_branch_dir = os.listdir(branch_install_dir)
            if self.lang_using.setup_file in contents_of_pkg_branch_dir:
                if download_pkg:
                    when_not_quiet_mode('Building & Installing {0} [{1}]...'.format(
                                                            pkg_to_install_name, branch_to_install), quiet)
                else:   # for turning branch back on
                    if verbose:
                        print('Reinstalling {0} [{1}]...'.format(pkg_to_install_name, branch_to_install))


                # make the log files directory for this pkg (need this for the record file)
                if not os.path.isdir(branch_logs_dir):
                    os.makedirs(branch_logs_dir)

                # see if the newly cloned dir installs properly
                return_val = self._cmd_output(install_cmd, verbose)

                if return_val == 0:
                    if download_pkg:
                        print('Successfully installed {0} [{1}].'.format(pkg_to_install_name, branch_to_install))
                    else:
                        if verbose:
                            print('Successfully reinstalled {0} [{1}].'.format(pkg_to_install_name, branch_to_install))


                    # if the pkg installed properly, then add the cmd that performed the installation to the database
                    #handle_db_after_an_install(self.pkg_type, pkg_to_install_name, branch_to_install, 
                                                #lang_cmd_for_install=self.lang_cmd,
                                                #db_pname=installation_db_path)

                else:   # if it isn't 0, then it failed to install

                    # show output with a failed install in normal output mode (in verbose mode it will 
                    # be printed out anyways from when trying to do the download and build).
                    if not verbose:    
                        try:
                            print('{0} {1}'.format(self.out.rstrip(), self.err.rstrip()))
                            print("\n\tCOULD NOT INSTALL {0} [{1}].".format(pkg_to_install_name, branch_to_install))
                            print("\tA likely cause is a dependancy issue.")
                            print("\t...see Traceback for information.")
                        except UnicodeEncodeError:
                            print("\n\tCOULD NOT INSTALL {0} [{1}].".format(pkg_to_install_name, branch_to_install))
                            print("\tA likely cause is a dependancy issue.")

                    if not download_pkg:
                        # remove the stuff for both download_pkg or not, but only print this stuff when trying to turn a package   
                        # back on (b/c when doing an install for the first time, the pkg won't have ever been used anyways).
                        print('Removing {0} [{1}].'.format(pkg_to_install_name, branch_to_install))
                        print("Reinstall a fresh install to use the package.")

                    # remove stuff with failed install                    
                    #shutil.rmtree(branch_install_dir)   # if the install didn't work, then remove the branch dir that was attempted to be downloaded & installed
                    #if not os.listdir(pkg_install_dir): # if the pkg install dir is empty, remove that
                        #os.rmdir(pkg_install_dir)
                    #if not os.listdir(self.pkg_type_install_dir): # if the pkg type install dir is empty, remove that
                        #os.rmdir(self.pkg_type_install_dir)
                    #if not os.listdir(self.lang_install_dir): # finally, if the lang install dir is empty, remove that
                        #shutil.rmtree(self.lang_install_dir)
                    self._remove_install_dirs(pkg_to_install_name, branch_to_install, pkg_install_dir, branch_install_dir, verbose)


                    #shutil.rmtree(branch_logs_dir)  # likewise, remove the pkg branch log dir
                    #if not os.listdir(pkg_logs_dir): # if the pkg logs dir is empty, remove that
                        #os.rmdir(pkg_logs_dir)
                    #if not os.listdir(self.pkg_type_logs_dir): # if the pkg type install dir is empty, remove that
                        #os.rmdir(self.pkg_type_logs_dir)
                    #if not os.listdir(self.lang_logs_dir): # finally, if the lang logs dir is empty, remove that
                        #shutil.rmtree(self.lang_logs_dir)
                    self._remove_log_dirs(pkg_to_install_name, branch_to_install, pkg_logs_dir, branch_logs_dir, verbose)


            else: 
                print(status("\tCANNOT INSTALL {0} [{1}].".format(pkg_to_install_name, branch_to_install)))
                print("\tThere is no {0} in this repo.".format(self.lang_using.setup_file))
                if not download_pkg:
                    print('Removing {0} [{1}].'.format(pkg_to_install_name, branch_to_install))
                    print("Reinstall a fresh install to use the package.")

                #shutil.rmtree(branch_install_dir)   # if the no setup file, then remove the branch dir that was attempted to be downloaded & installed
                #if not os.listdir(pkg_install_dir): # if the pkg install dir is empty, remove that
                    #os.rmdir(pkg_install_dir)
                #if not os.listdir(self.pkg_type_install_dir): # if the pkg type install dir is empty, remove that
                    #os.rmdir(self.pkg_type_install_dir)
                #if not os.listdir(self.lang_install_dir): # finally, if the lang install dir is empty, remove that
                    #shutil.rmtree(self.lang_install_dir)
                self._remove_install_dirs(pkg_to_install_name, branch_to_install, pkg_install_dir, branch_install_dir, verbose)


        if download_pkg:    # this is for the initial installation
            pkg_to_install_name, branch_to_install = self.parse_pkg_to_install_name(pkg_to_install)

            print('\n\n--> {0}  [branch: {1}]'.format(pkg_to_install_name, branch_to_install))

            should_it_be_installed = self._installation_check(self.pkg_type, pkg_to_install_name, branch_to_install, 
                                                                everything_already_installed)
            if should_it_be_installed:

                if not os.path.isdir(self.pkg_type_install_dir):
                    os.makedirs(self.pkg_type_install_dir)

                if not os.path.isdir(self.pkg_type_logs_dir):
                    os.makedirs(self.pkg_type_logs_dir) 

                download_success = self._download_pkg(pkg_to_install_name, branch_to_install, verbose)
                if download_success:
                    do_install(pkg_to_install_name, branch_to_install)

        else:  # don't have to download pkg first -- this is for turning pkg back on (from being turned off)
            # pkg_to_install is passed to the install func from the turn_on method & self.branch_to_turn_on_renamed is from turn_on 
            pkg_to_install_name = pkg_to_install
            branch_to_install = self.branch_to_turn_on_renamed
            do_install(pkg_to_install_name, branch_to_install) 


    def update(self, lang_to_update, pkg_to_update_name, branch_to_update, verbose):
        ''' updates the specified package's branch '''

        pkg_update_dir = join(self.pkg_type_install_dir, pkg_to_update_name)
        branch_update_dir = join(pkg_update_dir, branch_to_update)
        os.chdir(branch_update_dir)

        print('\n\n--> {0} [branch: {1}]'.format(pkg_to_update_name, branch_to_update))
        when_not_quiet_mode('Checking for updates...', quiet)

        return_val = self._cmd_output(self.update_cmd, verbose=False)
        if return_val != 0:
            try:
                print('{0} {1}'.format(self.out.rstrip(), self.err.rstrip()))
            except UnicodeEncodeError:
                pass
            print("\nCould not properly update {0} [{1}].".format(pkg_to_update_name, branch_to_update))
            print("Likely a network connection error.  Try again in a moment.")
            return

        output = self.out

        # do this b/c hg & bzr repos have multi-line output and the last item is all we want; for git 
        # it doesn't matter, there is only a one item output, so it will be what we want regardless.
        output_end = output.splitlines()[-1] 

        if self.up_to_date_output in output_end:    # this is if it's already up to date.
            #print(output_end)  # this is different for the different repo_types, so just print out a common thing:
            print('Already up to date.')
            return
        else:   # this is if it's not up to date (and if not, then update it here)
            if verbose:
                print(output.rstrip()) # prints all output from the pull

            # see if the package installs from the update correctly

            # use the same version of the language that was used to install the package to also update the package.
            record_file = self.lang_using._create_record_log_file(self.pkg_type_logs_dir, pkg_to_update_name, branch_to_update)
                # could also use the json db to get the lang for updating as well
            update_install_cmd = self.lang_using.get_install_cmd(pkg_to_update_name, branch_to_update, lang_to_update, record_file)

            contents_of_pkg_branch_dir = os.listdir(branch_update_dir)

            if self.lang_using.setup_file in contents_of_pkg_branch_dir:
                return_val = self._cmd_output(update_install_cmd, verbose)
            else:
                print("UPDATE FAILED for {0} [{1}].".format(pkg_to_update_name, branch_to_update))
                print("There is no longer a {0} to use for installing the package.".format(self.lang_using.setup_file))
                print("Try removing the package & then reinstalling it.")
                return

            if return_val == 0:
                ### combine the new log file just produced from the update with the other log file that 
                # already exists from the initial install (or a previous update); there will only be 
                # two log files at this point -- one older, perhaps already a combination of previous log 
                # files, and this newly created log file.  And when done with this, there will only be 
                # one log file again -- that which is a combination of all previous log files.

                pkg_logs_dir = join(self.pkg_type_logs_dir, pkg_to_update_name)
                branch_logs_dir = join(pkg_logs_dir, branch_to_update)

                record_fnames = glob.glob(join(branch_logs_dir, 'log_*.txt'))
                record_files = [open(rec_file, 'r').readlines() for rec_file in record_fnames]
                record_files_combined = list(set([rf for rf in itertools.chain.from_iterable(record_files)]))

                # create a new combined log file
                record_file = self.lang_using._create_record_log_file(self.pkg_type_logs_dir, pkg_to_update_name, branch_to_update)
                with open(record_file, 'w') as f: 
                    for i in record_files_combined:
                        f.write(i) 

                # delete all old logfiles, so that there is only the one combined log file that remains
                for rf in record_fnames:
                    os.remove(rf)

                print('Successfully updated {0} [{1}].'.format(pkg_to_update_name, branch_to_update))


            else:   # if not 0, then it failed to install properly
                if not verbose:    #  when in quiet mode, show output with a failed update installation to see the Traceback
                    try:
                        print('{0} {1}'.format(self.out.rstrip(), self.err.rstrip()))
                        print(status("\tUPDATE FAILED for {0} [{1}].".format(pkg_to_update_name, branch_to_update)))
                        print("\tA likely cause is a dependancy issue, eg. needing a (newer) dependancy.")
                        print("\t...see Traceback for information.")
                    except UnicodeEncodeError:
                        print(status("\tUPDATE FAILED for {0} [{1}].".format(pkg_to_update_name, branch_to_update)))
                        print("\tA likely cause is a dependancy issue, eg. needing a (newer) dependancy.")
                # TODO FIXME maybe something else needs to be done here -- like removing the update since it failed to install?


    def _remove_installed_files(self, pkg_to_remove_name, branch_to_remove_name, branch_installation_log_files, verbose):
        ''' remove the files installed in the userbase by using the install log file '''

        for branch_install_log in branch_installation_log_files: 
            ### *nix specific way that works
            #try: os.system('cat {0} | xargs rm -rf'.format(pkg_install_log))
            #except: pass

            # platform neutral way
            with open(branch_install_log, 'r') as install_log:
                for ln in install_log:
                    ln = ln.rstrip()
                    # not completely sure about this, but i think it works fine.
                    if os.path.exists(ln):
                        try:
                            if os.path.isfile(ln):
                                os.remove(ln)
                            elif os.path.isdir(ln):
                                shutil.rmtree(ln)#, ignore_errors=True)
                        except:
                            if verbose:
                                print("Error: Exception in removing {0} [{1}] {2}".format(pkg_to_remove_name, 
                                                                                        branch_to_remove_name, 
                                                                                        str(sys.exc_info())))
                    #else:
                        #print("Not found: {0}".format(ln))


    def _remove_empty_dirs_recursively(self, starting_dir, verbose):
        ''' recursively removes all empty dirs under the starting_dir '''
        for root, dirs, files in os.walk(starting_dir, topdown=False):
            for dir_name in dirs:
                d_path = join(root, dir_name)
                if not os.listdir(d_path): #to check wither the dir is empty
                    if verbose:
                        print("Deleting empty dir: {0}".format(d_path))
                    os.rmdir(d_path)


    def _remove_log_dirs(self, pkg_to_remove_name, branch_to_remove_name, pkg_logs_dir, branch_logs_dir, verbose):
        if verbose:
            print('Removing installation log files for {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name))
        if os.path.isdir(branch_logs_dir): # need this check for turned off branches (b/c if turned off, then this dir won't exist anyways)
            shutil.rmtree(branch_logs_dir)

        def remove_dir(dir_to_remove, str_out):
            if os.path.isdir(dir_to_remove): 
                if not os.listdir(dir_to_remove):
                    if verbose:
                        print(str_out)
                    shutil.rmtree(dir_to_remove)

        # checks whether a pkg_logs_dir is completely empty (meaning, there are no branches for the pkg), 
        # and if empty, then this removes the empty pkg_logs_dir 
        str_out = "Removing the package logs dir {0} because there are no branches in it...".format(pkg_to_remove_name)
        remove_dir(pkg_logs_dir, str_out)

        # likewise, this checks whether a pkg_type_logs_dir is completely empty (meaning, there are no packages
        # for the pkg type), and if empty, then this removes the empty pkg_type_log_dir. 
        str_out = "Removing the package type logs dir {0} because there are no packages in it...".format(self.pkg_type_logs_dir)
        remove_dir(self.pkg_type_logs_dir, str_out)

        # and the same goes for the lang_logs_dir 
        str_out = "Removing the language logs dir {0} because there are no package types in it...".format(self.lang_logs_dir)
        remove_dir(self.lang_logs_dir, str_out)


    def _remove_install_dirs(self, pkg_to_remove_name, branch_to_remove_name, pkg_dir, branch_dir, verbose):
        if verbose:
            print('Removing the downloaded package contents for {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name))
        shutil.rmtree(branch_dir)

        def remove_dir(dir_to_remove, str_out):
            if not os.listdir(dir_to_remove):
                if verbose:
                    print(str_out)
                shutil.rmtree(dir_to_remove)

        ### checks whether a pkg_dir is completely empty (meaning, there are no installed branches for the pkg), and 
        # if it is empty, then this removes the empty pkg_dir (its corresponding pkg_logs_dir is removed above).
        str_out = 'Removing the package dir {0} because there are no branches installed in it...'.format(pkg_to_remove_name)
        remove_dir(pkg_dir, str_out)

        ### likewise, this checks whether a pkg_type_install_dir is completely empty (meaning, there are no installed pkgs for the pkg type), 
        # and if it is empty, then this removes the empty pkg_type_install_dir (its corresponding pkg_type_logs_dir is removed above).
        str_out = 'Removing the package type dir {0} because there are no packages installed in it...'.format(self.pkg_type_install_dir)
        remove_dir(self.pkg_type_install_dir, str_out)

        ### and the same goes for the lang_install_dir as well.
        str_out = 'Removing the language install dir {0} because there are no packages installed in it...'.format(self.lang_install_dir)
        remove_dir(self.lang_install_dir, str_out)


    def remove(self, pkg_to_remove_name, branch_to_remove_name, verbose):
        ''' removes/uninstalls the specified package's branch, and if the last branch is removed from a package dir,
        then the package dir is removed as well.  Likewise, if the last package is removed from a package type, then
        the package type dir is removed.  Likewise for the language dir.  And the same procedure also goes for the 
        install_logs dirs; meaning, if they are empty, then they get removed too '''

        if branch_to_remove_name.startswith('.__'): 
            # for a branch that is turned off, need to make sure that the branches's dir (with ".__") is what is removed.
            actual_dir_name_for_branch_to_remove = branch_to_remove_name 
            branch_to_remove_name = branch_to_remove_name.lstrip('.__') 
        else:
            # for a branch that is turned on, this will be the same thing
            actual_dir_name_for_branch_to_remove = branch_to_remove_name

        when_not_quiet_mode('\nRemoving {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name), quiet) 

        # remove the installed branch from the installation area (the area produced from using --user)
        if verbose:
            print('Removing build & installation files for {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name))
        pkg_logs_dir = join(self.pkg_type_logs_dir, pkg_to_remove_name)
        branch_logs_dir = join(pkg_logs_dir, branch_to_remove_name)

        branch_installation_log_files = glob.glob(join(branch_logs_dir, 'log_*.txt')) # there should only be one (combined) logfile at any time.

        # uninstall all stuff installed for this branch, as indicated is installed via its install log file  
        self._remove_installed_files(pkg_to_remove_name, branch_to_remove_name, branch_installation_log_files, verbose)

        # remove the installation log files (and the subsequent empty dirs) just used.
        self._remove_log_dirs(pkg_to_remove_name, branch_to_remove_name, pkg_logs_dir, branch_logs_dir, verbose)

        # remove the downloaded branch from the pkg_dir (and the subsequent empty dirs).
        pkg_dir = join(self.pkg_type_install_dir, pkg_to_remove_name)
        branch_dir = join(pkg_dir, actual_dir_name_for_branch_to_remove)
        self._remove_install_dirs(pkg_to_remove_name, branch_to_remove_name, pkg_dir, branch_dir, verbose)

        # look recursively to see if the dirs in userbase are empty and remove those empty dirs.
        self._remove_empty_dirs_recursively(userbase, verbose)

        # remove the branch listing from the installation_db
        #if verbose:
            #print('Removing the {0} [{1}] listing from {2}...'.format(pkg_to_remove_name, branch_to_remove_name, installation_db))
        #handle_db_for_removal(self.pkg_type, pkg_to_remove_name, branch_to_remove_name, installation_db_path)

        print('Successfully uninstalled {0} [{1}].'.format(pkg_to_remove_name, branch_to_remove_name))
        #when_not_quiet_mode("Don't forget to remove {0}^{1} from your {2} file.".format(pkg_to_remove_name, branch_to_remove_name, packages_file), quiet)


    def turn_off(self, pkg_to_turn_off_name, branch_to_turn_off_name, verbose):
        ''' this makes the package inactive, so that other versions of the same package can be turned on or so  
        that a system level package of the same name (if there is one) can be used.  By being inactive, it hides 
        the installed pkg (by renaming it as, '.__branch_name'), so that it doesn't need to be re-downloaded &
        re-built if turned back on; note however, it does actually remove the stuff put into userbase to 
        remove the branches's files that were installed into the path.  This is nice b/c the downloads and builds 
        are what take so long for most package installations.'''

        when_not_quiet_mode('\nTurning off {0} [{1}]...'.format(pkg_to_turn_off_name, branch_to_turn_off_name), quiet) 

        # remove stuff from userbase with the log file 
        if verbose:
            print('Removing built & installed files for {0} [{1}]...'.format(pkg_to_turn_off_name, branch_to_turn_off_name))
        pkg_logs_dir = join(self.pkg_type_logs_dir, pkg_to_turn_off_name)
        branch_logs_dir = join(pkg_logs_dir, branch_to_turn_off_name)

        branch_installation_log_files = glob.glob(join(branch_logs_dir, 'log_*.txt')) # there should only be one (combined) logfile at any time.

        # uninstall all stuff installed for this branch, as indicated is installed via its install log file  
        self._remove_installed_files(pkg_to_turn_off_name, branch_to_turn_off_name, branch_installation_log_files, verbose)

        # remove the installation log files (and subsequent empty dirs) just used
        self._remove_log_dirs(pkg_to_turn_off_name, branch_to_turn_off_name, pkg_logs_dir, branch_logs_dir, verbose)

        # look recursively to see if the dirs in userbase are empty and removes those empty dirs.
        self._remove_empty_dirs_recursively(userbase, verbose)

        # rename the branch dir name (in the pkg_dir)
        if verbose:
            print('Renaming the downloaded package {0} [{1}]...'.format(pkg_to_turn_off_name, branch_to_turn_off_name))
        pkg_dir = join(self.pkg_type_install_dir, pkg_to_turn_off_name)
        branch_dir = join(pkg_dir, branch_to_turn_off_name)

        branch_to_turn_off_renamed = '.__{0}'.format(branch_to_turn_off_name)
        branch_to_turn_off_renamed_dir = join(pkg_dir, branch_to_turn_off_renamed)
        os.rename(branch_dir, branch_to_turn_off_renamed_dir)

        # rename the branch in the installation_db
        #if verbose:
            #print('Renaming the package {0} [{1}] in the {2} file...'.format(
                                                    #pkg_to_turn_off_name, branch_to_turn_off_name, installation_db))
        #handle_db_for_branch_renaming(self.pkg_type, pkg_to_turn_off_name, branch_to_turn_off_name, 
                                    #branch_to_turn_off_renamed, db_pname=installation_db_path)

        print('Successfully turned off {0} [{1}].'.format(pkg_to_turn_off_name, branch_to_turn_off_name))


    def _turn_on_check(self, pkg_type, pkg_to_turn_on_name, branch_to_turn_on, everything_already_installed):
        all_branches_installed_for_pkgs_lang_ver = branches_installed_for_given_pkgs_lang_ver(
                                                self.lang_cmd, 
                                                pkg_to_turn_on_name, everything_already_installed) 

        any_package_branch_on = [branch for branch in all_branches_installed_for_pkgs_lang_ver if not branch.startswith('.__')]

        for lang_installed, pkg_types_dict in everything_already_installed.items():
            if lang_installed == self.lang_cmd:
                for installed_pkg_type, pkgs_dict in pkg_types_dict.items():
                    for installed_pkg_name, branches_list in pkgs_dict.items(): 
                        if any_package_branch_on:
                            print("Cannot turn on {0} {1} [{2}] {3} because".format(pkg_type, pkg_to_turn_on_name, branch_to_turn_on, self.lang_cmd)) 
                            when_not_quiet_mode("a version of {0} is already turned on for {1}.".format(pkg_to_turn_on_name, self.lang_cmd), quiet) 
                            when_not_quiet_mode("[Execute `{} list` to see currently turned on packages.]".format(name), quiet)
                            return False
                        else:
                            return True


    def turn_on(self, pkg_to_turn_on_name, branch_to_turn_on_name, everything_already_installed, verbose):
        self.branch_to_turn_on_renamed = branch_to_turn_on_renamed = branch_to_turn_on_name.lstrip('.__')  

        when_not_quiet_mode('\nAttempting to turn on {0} [{1}]...'.format(pkg_to_turn_on_name, branch_to_turn_on_renamed), quiet) 

        should_turn_back_on = self._turn_on_check(self.pkg_type, pkg_to_turn_on_name, branch_to_turn_on_renamed, everything_already_installed)
        if should_turn_back_on: 

            # rename the branch dir name back to it's original name
            if verbose:
                print('Renaming {0} {1}...'.format(pkg_to_turn_on_name, branch_to_turn_on_renamed))

            pkg_dir = join(self.pkg_type_install_dir, pkg_to_turn_on_name)

            branch_dir_raw_name = join(pkg_dir, branch_to_turn_on_name)
            branch_dir_renamed = join(pkg_dir, branch_to_turn_on_renamed)

            os.rename(branch_dir_raw_name, branch_dir_renamed)

            # rename the branch back to it's original name in the installation_db
            #if verbose:
                #print('Renaming the package {0} [{1}] in the {2} file...'.format(
                                                    #pkg_to_turn_on_name, branch_to_turn_on_name, installation_db))
            #handle_db_for_branch_renaming(self.pkg_type, pkg_to_turn_on_name, branch_to_turn_on_name, 
                                        #branch_to_turn_on_renamed, db_pname=installation_db_path)

            # reinstall the branch files from the branch installation dir back into userbase
            if verbose:
                print('Reinstalling {0} {1}...'.format(pkg_to_turn_on_name, branch_dir_renamed))
            Package.install(self, pkg_to_turn_on_name, verbose, download_pkg=False)

            print('Successfully turned on {0} [{1}].'.format(pkg_to_turn_on_name, branch_to_turn_on_renamed))



class Git(Package):
    def __init__(self, lang_arg, pkg_type):
        self.repo_type = 'git'
        self.application_check_cmd = 'git --version'
        super(Git, self).__init__(lang_arg, pkg_type)
    
    def install(self, pkg_to_install, verbose, **kwargs):
        self.download_url_cmd = '-b {0} {1}'
        #self.install_download_cmd = 'git clone --single-branch {0}' # maybe want "git clone --recursive" instead?
        self.install_download_cmd = 'git clone {0} {1}' 
        Package.install(self, pkg_to_install, verbose, **kwargs)

    def update(self, lang_to_update, pkg_to_update, branch_to_update, verbose):
        #self.update_cmd = 'git pull && git submodule update --init --recursive'
        self.update_cmd = 'git pull'
        self.up_to_date_output = 'Already up-to-date'
        Package.update(self, lang_to_update, pkg_to_update, branch_to_update, verbose)


class Mercurial(Package):
    def __init__(self, lang_arg, pkg_type):
        self.repo_type = 'hg'
        self.application_check_cmd = 'hg --version'
        super(Mercurial, self).__init__(lang_arg, pkg_type)

    def install(self, pkg_to_install, verbose, **kwargs):
        #self.download_url_cmd = '-r {0} {1}' # need to look more into these commands
        self.download_url_cmd = '-b {0} {1}'
        self.install_download_cmd = 'hg clone {0} {1}'
        Package.install(self, pkg_to_install, verbose, **kwargs)

    def update(self, lang_to_update, pkg_to_update, branch_to_update, verbose):
        self.update_cmd = 'hg pull -u'
        self.up_to_date_output = 'no changes found'
        Package.update(self, lang_to_update, pkg_to_update, branch_to_update, verbose)


class Bazaar(Package):
    def __init__(self, lang_arg, pkg_type):
        self.repo_type = 'bzr'
        self.application_check_cmd = 'bzr --version'
        super(Bazaar, self).__init__(lang_arg, pkg_type)

    def install(self, pkg_to_install, verbose, **kwargs):
        self.download_url_cmd =  '{0} {1}'  # i think this is how you install a specific branch (not sure though)
        self.install_download_cmd = 'bzr branch {0} {1}'    # bzr uses branch instead of clone
        Package.install(self, pkg_to_install, verbose, **kwargs)

    def update(self, lang_to_update, pkg_to_update, branch_to_update, verbose):
        self.update_cmd = 'bzr pull'
        self.up_to_date_output = 'No revisions or tags to pull.'
        Package.update(self, lang_to_update, pkg_to_update, branch_to_update, verbose)


class RepoTypeCheck(Git, Mercurial, Bazaar):

    def install(self, pkg_to_install, verbose, **kwargs):
        self.repo_type, pkg_to_install = pkg_to_install.split('+')
        if self.repo_type == 'hg':
            Mercurial.install(self, pkg_to_install, verbose, **kwargs)
        elif self.repo_type == 'git':
            Git.install(self, pkg_to_install, verbose, **kwargs)
        elif self.repo_type == 'bzr':
            Bazaar.install(self, pkg_to_install, verbose, **kwargs)
        #elif <future_repo_type>:    # NOTE for other types of repos
            #<FutureRepoType.install(etc...)>
        else:   # should never hit this b/c it is(/should always be) covered in subclasses
            print("\nError installing {0}:".format(pkg_to_install))   
            print("Command to install packages needs to be specified as one of: {0}".format(self.allowed_repo_types))
            return

    def update(self, lang_to_update, pkg_to_update, branch_to_update, verbose):
        pkg_install_dir = join(self.pkg_type_install_dir, pkg_to_update)
        branch_install_dir = join(pkg_install_dir, branch_to_update)
        contents_of_branch_install_dir = os.listdir(branch_install_dir) 

        if '.hg' in contents_of_branch_install_dir:
            Mercurial.update(self, lang_to_update, pkg_to_update, branch_to_update, verbose)
        elif '.git' in contents_of_branch_install_dir:
            Git.update(self, lang_to_update, pkg_to_update, branch_to_update, verbose)
        elif '.bzr' in contents_of_branch_install_dir:
            Bazaar.update(self, lang_to_update, pkg_to_update, branch_to_update, verbose)
        #elif <future_repo_type>:    # NOTE for other types of repos
            #<FutureRepoType.update(etc...)>


class Github(Git):

    def install(self, pkg_to_install, verbose, **kwargs):
        #self.repo_type = 'git'
        self.allowed_repo_types = ['git']
        is_repo_type_specified = pkg_to_install.split('+')
        if len(is_repo_type_specified) == 2:
            #print("\nNote: do not have to specify repo type for Github repos.") 
            pkg_to_install = is_repo_type_specified[-1]

        self.download_url = 'https://github.com/{0}.git'
        Git.install(self, pkg_to_install, verbose, **kwargs)


class Gitorious(Git):
 
    def install(self, pkg_to_install, verbose, **kwargs):
        #self.repo_type = 'git'
        self.allowed_repo_types = ['git']
        is_repo_type_specified = pkg_to_install.split('+')
        if len(is_repo_type_specified) == 2:
            #print("\nNote: do not have to specify repo type for Gitorious repos.") 
            pkg_to_install = is_repo_type_specified[-1]

        self.download_url = 'http://git.gitorious.org/{0}.git'
        Git.install(self, pkg_to_install, verbose, **kwargs)


class Bitbucket(RepoTypeCheck):

    def install(self, pkg_to_install, verbose, **kwargs):
        self.allowed_repo_types = ['git', 'hg']
        self.repo_type = pkg_to_install.split('+')[0]
        if self.repo_type == 'hg': 
            self.download_url = 'https://bitbucket.org/{0}'
        elif self.repo_type == 'git':
            self.download_url = 'https://bitbucket.org/{0}.git'
        else:
            print("\nError installing {0}:".format(pkg_to_install))   
            print("Command to install {0} packages needs to be specified as one of: {1}".format(self.pkg_type, self.allowed_repo_types))
            return
        RepoTypeCheck.install(self, pkg_to_install, verbose, **kwargs)


class Local_Repo(RepoTypeCheck):
 
    def install(self, pkg_to_install, verbose, **kwargs):
        self.allowed_repo_types = ['git', 'hg', 'bzr']
        download_url_andor_branch = pkg_to_install.split('+')[-1].split('^')     # if specified w/ a branch: ['user/repo', 'branch']
        if len(download_url_andor_branch) == 2:     # means branch was specified
            print('\nError: Cannot specify branch for {0} installations.'.format(self.pkg_type)) 
            print("Just checkout desired branch from {0} first, then install.".format(self.pkg_type))
            return
        elif len(download_url_andor_branch) == 1:
            self.download_url = download_url_andor_branch[0]

        self.repo_type = pkg_to_install.split('+')[0]
        if self.repo_type not in self.allowed_repo_types: 
            print("\nError installing {0}:".format(pkg_to_install))   
            print("Command to install {0} packages needs to be specified as one of: {1}".format(self.pkg_type, self.allowed_repo_types))
            return
        RepoTypeCheck.install(self, pkg_to_install, verbose, **kwargs) 


# TODO to add in ability to use urls for ssh access and the like.
#class Remote_Repo(RepoTypeCheck):

    #def install(self, pkg_to_install, verbose):
        #self.allowed_repo_types = ['git', 'hg', 'bzr'] # maybe 'svn'?




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


def create_pkg_inst(lang_arg, pkg_type, packages_file=None):
    if pkg_type == 'github':
        return Github(lang_arg, pkg_type)

    elif pkg_type == 'bitbucket':
        return Bitbucket(lang_arg, pkg_type)

    elif pkg_type == 'gitorious':
        return Gitorious(lang_arg, pkg_type)

    elif pkg_type == 'local_repo':
        return Local_Repo(lang_arg, pkg_type)

    # NOTE for future pkg_types
    #elif pkg_type == <new/different_pkg_type>:
        #pkg_inst = new/different_pkg_type(lang_arg, pkg_type)
        #return pkg_inst

    if packages_file:  # installs from the pkgs file are the only thing that get this argument 
        not_pkg_type = status('{0} in your {1} is an unrecognized package type.\n'.format(pkg_type, packages_file))
        raise SystemExit(not_pkg_type)
    else:
        not_pkg_type = status('{0} is an unrecognized package type.\n'.format(pkg_type))
        raise SystemExit(not_pkg_type)


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



usr_home_dir = os.path.expanduser('~')  # specifies the user's home dir  
userbase = site.getuserbase()

#top_level_dir = join(options['top_level_dir'], '.{}'.format(name))
top_level_dir = join(usr_home_dir, '.{}'.format(name))

installed_pkgs_dir = join(top_level_dir, 'installed_pkgs') 
install_logs_dir = join(top_level_dir, '.install_logs') 

#installation_db = 'installation_db.json'
#installation_db_path = join(top_level_dir, installation_db)

packages_file = '.{}_packages'.format(name)
packages_file_path = join(usr_home_dir, packages_file)


def main(): # needs to be done as a main func for setuptools to work correctly in creating an executable
    
    import argparse     #http://docs.python.org/2/library/argparse.html
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


    verbose = args.verbose

    global quiet
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
    if quiet:
        print('-'*60)

    everything_already_installed = all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir)
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
                when_not_quiet_mode(status('\t\tInstalling {0} packages'.format(pkg_type)), quiet)

                if len(pkgs_from_pkgs_file) >= 1:

                    for pkg_to_install in pkgs_from_pkgs_file: 

                        lang_and_pkg_to_install = pkg_to_install.split('-->')  # to see if a language is given 
                        if len(lang_and_pkg_to_install) == 2:
                            lang_arg, pkg_to_install = lang_and_pkg_to_install
                            pkg_inst = create_pkg_inst(lang_arg, pkg_type, packages_file)
                        elif len(lang_and_pkg_to_install) != 2:
                            print("\nError: need to specifiy a language in {0} for:".format(packages_file)) 
                            print("\t{}".format(pkg_to_install))
                            raise SystemExit


                        # important to see what has previously been installed, so as to not turn on a 2nd version of a package.
                        everything_already_installed = all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir) 
                        pkg_inst.install(pkg_to_install, verbose, 
                                            everything_already_installed=everything_already_installed)
                else:
                    when_not_quiet_mode('\nNo {0} packages specified in {1} to install.'.format(pkg_type, packages_file), quiet)

        # install w/ command line arg(s)
        elif install_arg != packages_file_path:  

            pkg_type_with_pkg_to_process = []   # this will be a list of tuples 
            for pkg_type_and_pkg_to_process in install_arg:
                pkg_type_andor_pkg_to_process = pkg_type_and_pkg_to_process.split('=') # need this check b/c pkg_type has to be specified when using cmdline 
                if len(pkg_type_andor_pkg_to_process) != 2:
                    how_to_specify_installation(pkg_type_andor_pkg_to_process[0])
                    #continue
                    raise SystemExit
                pkg_type, pkg_to_process = pkg_type_andor_pkg_to_process
                pkg_type_with_pkg_to_process.append((pkg_type, pkg_to_process))


            for pkg_type, pkg_to_install in pkg_type_with_pkg_to_process:

                pkg_to_install_specified_with_user_and_repo = pkg_to_install.split('/')
                if len(pkg_to_install_specified_with_user_and_repo) == 1:
                    print("\nError: need to specifiy a user and branch for {}, like:".format(pkg_to_install))
                    print("\t{} install github=git+username/pkg_name[^optional_branch]".format(name))   
                    raise SystemExit

                when_not_quiet_mode(status('\t\tInstalling {0} package'.format(pkg_type)), quiet)
                pkg_inst = create_pkg_inst(lang_arg, pkg_type)

                # important to keep this here so it can be known what has previously been installed, so as to not turn on a 2nd version of a package.
                everything_already_installed = all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir) 
                pkg_inst.install(pkg_to_install, verbose, 
                                    everything_already_installed=everything_already_installed)

    


    # list installed pkg(s) (by each package type)
    elif 'list_arg' in args:
        if everything_already_installed:

            count_of_listed = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():

                if not lang_arg:  # if a language arg is not given, then list all installed packages
                    when_not_quiet_mode("\n{0} packages installed:".format(lang_dir_name), quiet)

                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    #if not lang_arg:  # if a language arg is given, then remove all pkgs for that lang's version
                        #when_not_quiet_mode("\t{0}:".format(pkg_type), quiet)

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
                            pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                            lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                            if lang_dir_name == lang_cmd:
                                count_of_listed = list_packages()
                        else:
                            count_of_listed = list_packages()

            if count_of_listed == 0: 
                when_not_quiet_mode('\n[ No packages for listing ]'.format(pkg_type), quiet) 
        else:
            print('\nNo packages installed.') 



    # update pkg(s)
    elif 'update_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_updated = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                        pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                        pkgs_and_branches_off = pkgs_status['pkg_branches_off']

                        if update_arg == 'ALL':
                            if lang_arg:  # if a language arg is given, then update all pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    when_not_quiet_mode(status('\t\tUpdating {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                    count_of_pkgs_updated = 0
                                    for pkg_to_update, branch_on in pkgs_and_branches_on.items():
                                        for branch_to_update in branch_on:
                                            pkg_inst.update(lang_dir_name, pkg_to_update, branch_to_update, verbose)
                                            count_of_pkgs_updated += 1
                                            top_count_of_pkgs_updated += 1

                                    if count_of_pkgs_updated == 0:
                                        when_not_quiet_mode('\nNo {0} {1} packages turned on for updating.'.format(lang_dir_name, pkg_type), quiet) 
                                        top_count_of_pkgs_updated = -1

                            else:  # if no language arg is given, then just update all installed pkgs
                                when_not_quiet_mode(status('\t\tUpdating {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type)

                                count_of_pkgs_updated = 0
                                for pkg_to_update, branch_on in pkgs_and_branches_on.items():
                                    for branch_to_update in branch_on:
                                        pkg_inst.update(lang_dir_name, pkg_to_update, branch_to_update, verbose)
                                        count_of_pkgs_updated += 1
                                        top_count_of_pkgs_updated += 1

                                if count_of_pkgs_updated == 0:
                                    when_not_quiet_mode('\nNo {0} {1} packages turned on for updating.'.format(lang_dir_name, pkg_type), quiet) 
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
                                                    print("\nUpdate {0} {1} with:".format(pkg_to_update, lang_installed))
                                                    print("\t{0} -l {1} update {2}={3}".format(name, lang_installed, 
                                                                            pkg_type_installed, pkg_name_installed))
                                                else:
                                                    print("\nUpdate {0} [{1}] {2} with:".format(pkg_to_update, branch_installed, 
                                                                                                    lang_installed))
                                                    print("\t{0} -l {1} update {2}={3}^{4}".format(name, lang_installed,
                                                                            pkg_type_installed, pkg_name_installed, branch_installed))

                                            elif branch_installed.startswith('.__'): 
                                                branch_installed = branch_installed.lstrip('.__')
                                                print("\n{0} [{1}] {2} turned off:  turn on to update.".format(
                                                                                    pkg_name_installed, branch_installed, lang_installed))
                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def update_branch(pkg_to_update, branch_to_update, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
                                if lang_dir_name == lang_cmd:
                                    for pkg_name, branch_on in pkgs_and_branches_on.items():
                                        if pkg_name == pkg_to_update: 
                                            if branch_to_update in branch_on: 
                                                when_not_quiet_mode(status('\tUpdating {0} [{1}] {2} {3}'.format(
                                                        pkg_to_update, branch_to_update, lang_dir_name, pkg_type)), quiet)
                                                pkg_inst.update(lang_cmd, pkg_to_update, branch_to_update, verbose)
                                                was_pkg_processed = True

                                    for pkg_name, branches_off in pkgs_and_branches_off.items():
                                        if pkg_name == pkg_to_update: 
                                            if branch_to_update in branches_off: 
                                                branch_installed = branch_to_update.lstrip('.__')
                                                print("\n{0} [{1}] {2} turned off:  turn on to update.".format(
                                                                                    pkg_name, branch_installed, lang_cmd))
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_updated = package_processor(lang_arg,
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
                when_not_quiet_mode('\n[ No packages specified for updating ]'.format(pkg_type), quiet) 
        else:
            print('\nNo packages installed.') 



    # remove pkg(s) 
    elif 'remove_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_removed = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                        pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                        pkgs_and_branches_off = pkgs_status['pkg_branches_off']


                        def remove_turned_off_branches(top_count_of_pkgs_removed, count_of_pkgs_removed=0):
                            for pkg_to_remove, branches_off in pkgs_and_branches_off.items():
                                for branch_to_remove in branches_off:
                                    branch_to_remove = '.__{0}'.format(branch_to_remove)
                                    pkg_inst.remove(pkg_to_remove, branch_to_remove, verbose)
                                    count_of_pkgs_removed += 1; top_count_of_pkgs_removed += 1
                            return count_of_pkgs_removed

                        def remove_turned_on_branches(top_count_of_pkgs_removed, count_of_pkgs_removed=0):
                            for pkg_to_remove, branch_on in pkgs_and_branches_on.items():
                                for branch_to_remove in branch_on:
                                    pkg_inst.remove(pkg_to_remove, branch_to_remove, verbose)
                                    count_of_pkgs_removed += 1; top_count_of_pkgs_removed += 1
                            return count_of_pkgs_removed


                        if remove_arg == 'ALL':
                            if lang_arg:  # if a language arg is given, then remove all pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    when_not_quiet_mode(status('\t\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                    count_of_turned_on_removed = remove_turned_on_branches(top_count_of_pkgs_removed)
                                    count_of_turned_off_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                    if (count_of_turned_on_removed or count_of_turned_off_removed):
                                        top_count_of_pkgs_removed = -1


                            else:  # if no language arg is given, then remove all installed pkgs
                                when_not_quiet_mode(status('\t\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type)
                                count_of_turned_on_removed = remove_turned_on_branches(top_count_of_pkgs_removed)
                                count_of_turned_off_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                if (count_of_turned_on_removed or count_of_turned_off_removed):
                                    top_count_of_pkgs_removed = -1


                        elif remove_arg == 'turned_off':
                            if lang_arg:  # if a language arg is given, then remove all turned off pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    when_not_quiet_mode(status('\tRemoving turned off {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                    count_of_pkgs_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                    if count_of_pkgs_removed == 0:
                                        when_not_quiet_mode('\nNo {0} {1} packages turned off for removal.'.format(lang_dir_name, pkg_type), quiet) 
                                        top_count_of_pkgs_removed = -1

                            else:  # if no language arg is given, then remove all turned off pkgs
                                when_not_quiet_mode(status('\tRemoving {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type)
                                count_of_pkgs_removed = remove_turned_off_branches(top_count_of_pkgs_removed)
                                if count_of_pkgs_removed == 0:
                                    when_not_quiet_mode('\nNo {0} {1} packages turned off for removal.'.format(lang_dir_name, pkg_type), quiet) 
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
                                                print("\nRemove {0} {1} with:".format(pkg_to_remove, lang_installed))
                                                print("\t{0} -l {1} remove {2}={3}".format(name, lang_installed, 
                                                                        pkg_type_installed, pkg_name_installed))
                                            else:
                                                print("\nRemove {0} [{1}] {2} with:".format(pkg_to_remove, branch_installed, 
                                                                                                lang_installed))
                                                print("\t{0} -l {1} remove {2}={3}^{4}".format(name, lang_installed,
                                                                        pkg_type_installed, pkg_name_installed, branch_installed))

                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def remove_branch(pkg_to_remove, branch_to_remove, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
                                if lang_dir_name == lang_cmd:
                                    for pkg_name, branch_on in pkgs_and_branches_on.items():
                                        if pkg_name == pkg_to_remove: 
                                            if branch_to_remove in branch_on: 
                                                when_not_quiet_mode(status('\tRemoving {0} [{1}] {2} {3}'.format(
                                                        pkg_to_remove, branch_to_remove, lang_dir_name, pkg_type)), quiet)
                                                pkg_inst.remove(pkg_to_remove, branch_to_remove, verbose)
                                                was_pkg_processed = True

                                    for pkg_name, branches_off in pkgs_and_branches_off.items():
                                        if pkg_name == pkg_to_remove: 
                                            if branch_to_remove in branches_off: 
                                                when_not_quiet_mode(status('\tRemoving {0} [{1}] {2} {3}'.format(
                                                        pkg_to_remove, branch_to_remove, lang_dir_name, pkg_type)), quiet)
                                                branch_to_remove = '.__{0}'.format(branch_to_remove)
                                                pkg_inst.remove(pkg_to_remove, branch_to_remove, verbose)
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_removed = package_processor(lang_arg,
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
                when_not_quiet_mode('\n[ No packages specified for removing ]'.format(pkg_type), quiet) 
        else:
            print('\nNo packages installed.') 




    # turn off pkg(s) 
    elif 'turn_off_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_turned_off = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                        pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                        pkgs_and_branches_off = pkgs_status['pkg_branches_off']


                        def turn_off_branches(top_count_of_pkgs_turned_off, count_of_pkgs_turned_off=0):
                            for pkg_to_turn_off, branch_on in pkgs_and_branches_on.items():
                                for branch_to_turn_off in branch_on:
                                    pkg_inst.turn_off(pkg_to_turn_off, branch_to_turn_off, verbose)
                                    count_of_pkgs_turned_off += 1; top_count_of_pkgs_turned_off += 1
                            return count_of_pkgs_turned_off


                        if turn_off_arg == 'ALL':
                            if lang_arg:  # if a language arg is given, then turn off all pkgs for that lang's version
                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version

                                if lang_dir_name == lang_cmd:
                                    when_not_quiet_mode(status('\t\tTurning off {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                    count_of_turned_off = turn_off_branches(top_count_of_pkgs_turned_off)
                                    if count_of_turned_off:
                                        top_count_of_pkgs_turned_off = -1

                            else:  # if no language arg is given, then turn off all installed pkgs
                                when_not_quiet_mode(status('\t\tTurning off {0} {1} packages'.format(lang_dir_name, pkg_type)), quiet)
                                pkg_inst = create_pkg_inst(lang_dir_name, pkg_type)
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
                                                    print("\nTurn off {0} {1} with:".format(pkg_to_turn_off, lang_installed))
                                                    print("\t{0} -l {1} turn_off {2}={3}".format(name, lang_installed, 
                                                                            pkg_type_installed, pkg_name_installed))
                                                else:
                                                    print("\nTurn off {0} [{1}] {2} with:".format(pkg_to_turn_off, branch_installed, 
                                                                                                    lang_installed))
                                                    print("\t{0} -l {1} turn_off {2}={3}^{4}".format(name, lang_installed,
                                                                            pkg_type_installed, pkg_name_installed, branch_installed))

                                            elif branch_installed.startswith('.__'): 
                                                branch_installed = branch_installed.lstrip('.__')
                                                print("\n{0} [{1}] {2} already turned off.".format(pkg_name_installed, branch_installed, lang_installed))

                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def turn_off_branch(pkg_to_turn_off, branch_to_turn_off, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
                                lang_cmd = pkg_inst.lang_cmd  # makes it so that the system default of a lang maps back on to it's particular version
                                if lang_dir_name == lang_cmd:
                                    for pkg_name, branch_on in pkgs_and_branches_on.items():
                                        if pkg_name == pkg_to_turn_off: 
                                            if branch_to_turn_off in branch_on: 
                                                when_not_quiet_mode(status('\tTurning off {0} [{1}] {2} {3}'.format(
                                                        pkg_to_turn_off, branch_to_turn_off, lang_dir_name, pkg_type)), quiet)
                                                pkg_inst.turn_off(pkg_to_turn_off, branch_to_turn_off, verbose)
                                                was_pkg_processed = True

                                    for pkg_name, branches_off in pkgs_and_branches_off.items():
                                        if pkg_name == pkg_to_turn_off: 
                                            if branch_to_turn_off in branches_off: 
                                                #branch_installed = branch_to_turn_off.lstrip('.__')
                                                print('\n{0} [{1}] {2} already turned off.'.format(pkg_to_turn_off, branch_to_turn_off, lang_cmd)) 
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_turned_off = package_processor(lang_arg,
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
                when_not_quiet_mode('\n[ No packages specified for turning off ]'.format(pkg_type), quiet) 
        else:
            print('\nNo packages installed.') 


    # turn on pkg(s) 
    elif 'turn_on_arg' in args:
        if everything_already_installed:

            top_count_of_pkgs_turned_on = 0
            for lang_dir_name, pkg_type_dict in everything_already_installed.items():
                for pkg_type, pkgs_and_branches in pkg_type_dict.items():

                    if len(pkgs_and_branches) >= 1:
                        pkgs_status = pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
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
                                                    print("\nTurn on {0} {1} with:".format(pkg_to_turn_on, lang_installed))
                                                    print("\t{0} -l {1} turn_on {2}={3}".format(name, lang_installed, 
                                                                            pkg_type_installed, pkg_name_installed))
                                                else:
                                                    print("\nTurn on {0} [{1}] {2} with:".format(pkg_to_turn_on, branch_installed, 
                                                                                                    lang_installed))
                                                    print("\t{0} -l {1} turn_on {2}={3}^{4}".format(name, lang_installed,
                                                                            pkg_type_installed, pkg_name_installed, branch_installed))

                                            elif not branch_installed.startswith('.__'): 
                                                print("\n{0} [{1}] {2} already turned on.".format(pkg_name_installed, branch_installed, lang_installed))
                                            how_to_count += 1

                                if how_to_count == 0:
                                    return 0
                                else:
                                    return -1


                            def turn_on_branch(pkg_to_turn_on, branch_to_turn_on, was_pkg_processed):

                                pkg_inst = create_pkg_inst(lang_arg, pkg_type)
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
                                                when_not_quiet_mode(status('\tTurning on {0} [{1}] {2} {3}'.format(
                                                        pkg_to_turn_on, branch_to_turn_on, lang_dir_name, pkg_type)), quiet)
                                                branch_to_turn_on = '.__{0}'.format(branch_to_turn_on)
                                                pkg_inst.turn_on(pkg_to_turn_on, branch_to_turn_on, everything_already_installed, verbose)
                                                was_pkg_processed = True

                                    return was_pkg_processed


                            was_pkg_turned_on = package_processor(lang_arg,
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
                when_not_quiet_mode('\n[ No packages specified for turning on ]'.format(pkg_type), quiet) 
        else:
            print('\nNo packages installed.') 
