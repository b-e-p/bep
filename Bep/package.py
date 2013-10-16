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
import site
import shutil
import subprocess
import sys 
import glob
import itertools
import locale   # needed in py3 for decoding output from subprocess pipes 
import Bep.languages as languages
from Bep.core.release_info import name
#from core.utils_db import (handle_db_after_an_install, handle_db_for_removal,
                        #handle_db_for_branch_renaming,
                        #get_lang_cmd_branch_was_installed_with)
import utils


class Package(object):
    def __init__(self, lang_arg, pkg_type, install_dirs, **kwargs):

        if 'python' in lang_arg:
            self.lang_using = languages.Python()
        #elif 'otherlanguage' in lang_arg:  # for other languages
            #self.lang_using = languages.OtherLanguage()
        else:
            print("\nError: {0} currently not supported.".format(lang_arg))
            raise SystemExit

        self.lang_cmd = self.lang_using.get_lang_cmd(lang_arg)

        self.pkg_type = pkg_type

        self.installed_pkgs_dir = install_dirs['installed_pkgs_dir']
        self.install_logs_dir = install_dirs['install_logs_dir']  

        self.lang_install_dir = join(self.installed_pkgs_dir, self.lang_cmd)
        self.lang_logs_dir = join(self.install_logs_dir, self.lang_cmd)

        self.pkg_type_install_dir = join(self.lang_install_dir, self.pkg_type) 
        self.pkg_type_logs_dir = join(self.lang_logs_dir, self.pkg_type) 


    def _cmd_output(self, cmd, verbose):
        encoding = locale.getdefaultlocale()[1]     # py3 stuff b/c this is encoded as b('...')
        if verbose:    # shows all the output when running cmd -- sometimes lots of stuff
            print(cmd)
            cmd = cmd.split(' ') # to use w/o setting needing to set shell=True
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout:
                line = line.decode(encoding)
                print(line.rstrip())
            return_val = p.wait()

        else:   # for a quiet mode -- only shows the output when the cmd fails
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
        assert len(pkg_branch_test) <= 2, "Only allowed to specify one branch/version per package listing for installation."
        if len(pkg_branch_test) == 2:
            pkg_to_install, branch = pkg_branch_test
            pkg_to_install = strip_end_of_str(pkg_to_install) 

            if len(pkg_to_install.split('/')) == 1:
                utils.how_to_specify_installation(pkg_to_install)
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


    def _download_pkg(self, pkg_to_install_name, branch_to_install_name, noise):
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

        utils.when_not_quiet_mode('Downloading {0} [{1}]...'.format(pkg_to_install_name, branch_to_install_name), noise.quiet)

        # download the branch to the pkg_name_dir 
        os.chdir(pkg_name_dir)
        return_val = self._cmd_output(self.install_download_cmd, verbose=noise.verbose)

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

        all_branches_installed_for_pkgs_lang_ver = utils.branches_installed_for_given_pkgs_lang_ver(
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



    def install(self, pkg_to_install, noise, download_pkg=True, everything_already_installed=None):
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
                    utils.when_not_quiet_mode('Building & Installing {0} [{1}]...'.format(
                                                            pkg_to_install_name, branch_to_install), noise.quiet)
                else:   # for turning branch back on
                    if noise.verbose:
                        print('Reinstalling {0} [{1}]...'.format(pkg_to_install_name, branch_to_install))


                # make the log files directory for this pkg (need this for the record file)
                if not os.path.isdir(branch_logs_dir):
                    os.makedirs(branch_logs_dir)

                # see if the newly cloned dir installs properly
                return_val = self._cmd_output(install_cmd, verbose=noise.verbose)

                if return_val == 0:
                    if download_pkg:
                        print('Successfully installed {0} [{1}].'.format(pkg_to_install_name, branch_to_install))
                    else:
                        if noise.verbose:
                            print('Successfully reinstalled {0} [{1}].'.format(pkg_to_install_name, branch_to_install))


                    # if the pkg installed properly, then add the cmd that performed the installation to the database
                    #handle_db_after_an_install(self.pkg_type, pkg_to_install_name, branch_to_install, 
                                                #lang_cmd_for_install=self.lang_cmd,
                                                #db_pname=installation_db_path)

                else:   # if it isn't 0, then it failed to install

                    # show output with a failed install in normal output mode (in verbose mode it will 
                    # be printed out anyways from when trying to do the download and build).
                    if not noise.verbose:    
                        try:
                            print('{0} {1}'.format(self.out.rstrip(), self.err.rstrip()))
                            print("\n\tCOULD NOT INSTALL {0} [{1}].".format(pkg_to_install_name, branch_to_install))
                            print("\tA likely cause is a dependency issue.")
                            print("\t...see Traceback for information.")
                        except UnicodeEncodeError:
                            print("\n\tCOULD NOT INSTALL {0} [{1}].".format(pkg_to_install_name, branch_to_install))
                            print("\tA likely cause is a dependency issue.")

                    if not download_pkg:
                        # remove the stuff for both download_pkg or not, but only print this stuff when trying to turn a package   
                        # back on (b/c when doing an install for the first time, the pkg won't have ever been used anyways).
                        print('Removing {0} [{1}].'.format(pkg_to_install_name, branch_to_install))
                        print("Reinstall a fresh install to use the package.")

                    # remove stuff with failed install                    
                    self._remove_install_dirs(pkg_to_install_name, branch_to_install, pkg_install_dir, branch_install_dir, noise)

                    # likewise, remove the pkg branch log dir
                    self._remove_log_dirs(pkg_to_install_name, branch_to_install, pkg_logs_dir, branch_logs_dir, noise)


            else: 
                print("\n\tCANNOT INSTALL {0} [{1}].".format(pkg_to_install_name, branch_to_install))
                print("\tThere is no {0} in this repo.".format(self.lang_using.setup_file))
                if not download_pkg:
                    print('Removing {0} [{1}].'.format(pkg_to_install_name, branch_to_install))
                    print("Reinstall a fresh install to use the package.")

                # if the no setup file, then remove the branch dir that was attempted to be downloaded & installed
                self._remove_install_dirs(pkg_to_install_name, branch_to_install, pkg_install_dir, branch_install_dir, noise)


        if download_pkg:    # this is for the initial installation
            pkg_to_install_name, branch_to_install = self.parse_pkg_to_install_name(pkg_to_install)

            print('\n--> {0}  [{1}]'.format(pkg_to_install_name, branch_to_install))

            should_it_be_installed = self._installation_check(self.pkg_type, pkg_to_install_name, branch_to_install, 
                                                                everything_already_installed)
            if should_it_be_installed:

                if not os.path.isdir(self.pkg_type_install_dir):
                    os.makedirs(self.pkg_type_install_dir)

                if not os.path.isdir(self.pkg_type_logs_dir):
                    os.makedirs(self.pkg_type_logs_dir) 

                download_success = self._download_pkg(pkg_to_install_name, branch_to_install, noise)
                if download_success:
                    do_install(pkg_to_install_name, branch_to_install)

        else:  # don't have to download pkg first -- this is for turning pkg back on (from being turned off)
            # pkg_to_install is passed to the install func from the turn_on method & self.branch_to_turn_on_renamed is from turn_on 
            pkg_to_install_name = pkg_to_install
            branch_to_install = self.branch_to_turn_on_renamed
            do_install(pkg_to_install_name, branch_to_install) 


    def update(self, lang_to_update, pkg_to_update_name, branch_to_update, noise):
        ''' updates the specified package's branch '''

        pkg_update_dir = join(self.pkg_type_install_dir, pkg_to_update_name)
        branch_update_dir = join(pkg_update_dir, branch_to_update)
        os.chdir(branch_update_dir)

        print('\n--> {0} [{1}]'.format(pkg_to_update_name, branch_to_update))
        utils.when_not_quiet_mode('Checking for updates...', noise.quiet)

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
            if noise.verbose:
                print(output.rstrip()) # prints all output from the pull

            # see if the package installs from the update correctly

            # use the same version of the language that was used to install the package to also update the package.
            record_file = self.lang_using._create_record_log_file(self.pkg_type_logs_dir, pkg_to_update_name, branch_to_update)
                # could also use the json db to get the lang for updating as well
            update_install_cmd = self.lang_using.get_install_cmd(pkg_to_update_name, branch_to_update, lang_to_update, record_file)

            contents_of_pkg_branch_dir = os.listdir(branch_update_dir)

            if self.lang_using.setup_file in contents_of_pkg_branch_dir:
                return_val = self._cmd_output(update_install_cmd, verbose=noise.verbose)
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
                if not noise.verbose:    #  when in quiet mode, show output with a failed update installation to see the Traceback
                    try:
                        print('{0} {1}'.format(self.out.rstrip(), self.err.rstrip()))
                        print(utils.status("\tUPDATE FAILED for {0} [{1}].".format(pkg_to_update_name, branch_to_update)))
                        print("\tA likely cause is a dependency issue, eg. needing a (newer) dependency.")
                        print("\t...see Traceback for information.")
                    except UnicodeEncodeError:
                        print(utils.status("\tUPDATE FAILED for {0} [{1}].".format(pkg_to_update_name, branch_to_update)))
                        print("\tA likely cause is a dependency issue, eg. needing a (newer) dependency.")
                # TODO FIXME maybe something else needs to be done here -- like removing the update since it failed to install?


    def _remove_installed_files(self, pkg_to_remove_name, branch_to_remove_name, branch_installation_log_files, noise):
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
                            if noise.verbose:
                                print("Error: Exception in removing {0} [{1}] {2}".format(pkg_to_remove_name, 
                                                                                        branch_to_remove_name, 
                                                                                        str(sys.exc_info())))
                    #else:
                        #print("Not found: {0}".format(ln))


    def _remove_empty_dirs_recursively(self, starting_dir, noise):
        ''' recursively removes all empty dirs under the starting_dir '''
        for root, dirs, files in os.walk(starting_dir, topdown=False):
            for dir_name in dirs:
                d_path = join(root, dir_name)
                if not os.listdir(d_path): #to check wither the dir is empty
                    if noise.verbose:
                        print("Deleting empty dir: {0}".format(d_path))
                    os.rmdir(d_path)


    def _remove_log_dirs(self, pkg_to_remove_name, branch_to_remove_name, pkg_logs_dir, branch_logs_dir, noise):
        if noise.verbose:
            print('Removing installation log files for {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name))
        if os.path.isdir(branch_logs_dir): # need this check for turned off branches (b/c if turned off, then this dir won't exist anyways)
            shutil.rmtree(branch_logs_dir)

        def remove_dir(dir_to_remove, str_out):
            if os.path.isdir(dir_to_remove): 
                if not os.listdir(dir_to_remove):
                    if noise.verbose:
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


    def _remove_install_dirs(self, pkg_to_remove_name, branch_to_remove_name, pkg_dir, branch_dir, noise):
        if noise.verbose:
            print('Removing the downloaded package contents for {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name))
        shutil.rmtree(branch_dir)

        def remove_dir(dir_to_remove, str_out):
            if not os.listdir(dir_to_remove):
                if noise.verbose:
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


    def remove(self, pkg_to_remove_name, branch_to_remove_name, noise):
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

        utils.when_not_quiet_mode('\nRemoving {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name), noise.quiet) 

        # remove the installed branch from the installation area (the area produced from using --user)
        if noise.verbose:
            print('Removing build & installation files for {0} [{1}]...'.format(pkg_to_remove_name, branch_to_remove_name))
        pkg_logs_dir = join(self.pkg_type_logs_dir, pkg_to_remove_name)
        branch_logs_dir = join(pkg_logs_dir, branch_to_remove_name)

        branch_installation_log_files = glob.glob(join(branch_logs_dir, 'log_*.txt')) # there should only be one (combined) logfile at any time.

        # uninstall all stuff installed for this branch, as indicated is installed via its install log file  
        self._remove_installed_files(pkg_to_remove_name, branch_to_remove_name, branch_installation_log_files, noise)

        # remove the installation log files (and the subsequent empty dirs) just used.
        self._remove_log_dirs(pkg_to_remove_name, branch_to_remove_name, pkg_logs_dir, branch_logs_dir, noise)

        # remove the downloaded branch from the pkg_dir (and the subsequent empty dirs).
        pkg_dir = join(self.pkg_type_install_dir, pkg_to_remove_name)
        branch_dir = join(pkg_dir, actual_dir_name_for_branch_to_remove)
        self._remove_install_dirs(pkg_to_remove_name, branch_to_remove_name, pkg_dir, branch_dir, noise)

        # look recursively to see if the dirs in userbase are empty and remove those empty dirs.
        self._remove_empty_dirs_recursively(site.getuserbase(), noise)

        # remove the branch listing from the installation_db
        #if noise.verbose:
            #print('Removing the {0} [{1}] listing from {2}...'.format(pkg_to_remove_name, branch_to_remove_name, installation_db))
        #handle_db_for_removal(self.pkg_type, pkg_to_remove_name, branch_to_remove_name, installation_db_path)

        print('Successfully uninstalled {0} [{1}].'.format(pkg_to_remove_name, branch_to_remove_name))
        #when_not_quiet_mode("Don't forget to remove {0}^{1} from your {2} file.".format(pkg_to_remove_name, branch_to_remove_name, packages_file), noise.quiet)


    def turn_off(self, pkg_to_turn_off_name, branch_to_turn_off_name, noise):
        ''' this makes the package inactive, so that other versions of the same package can be turned on or so  
        that a system level package of the same name (if there is one) can be used.  By being inactive, it hides 
        the installed pkg (by renaming it as, '.__branch_name'), so that it doesn't need to be re-downloaded &
        re-built if turned back on; note however, it does actually remove the stuff put into userbase to 
        remove the branches's files that were installed into the path.  This is nice b/c the downloads and builds 
        are what take so long for most package installations.'''

        utils.when_not_quiet_mode('\nTurning off {0} [{1}]...'.format(pkg_to_turn_off_name, branch_to_turn_off_name), noise.quiet) 

        # remove stuff from userbase with the log file 
        if noise.verbose:
            print('Removing built & installed files for {0} [{1}]...'.format(pkg_to_turn_off_name, branch_to_turn_off_name))
        pkg_logs_dir = join(self.pkg_type_logs_dir, pkg_to_turn_off_name)
        branch_logs_dir = join(pkg_logs_dir, branch_to_turn_off_name)

        branch_installation_log_files = glob.glob(join(branch_logs_dir, 'log_*.txt')) # there should only be one (combined) logfile at any time.

        # uninstall all stuff installed for this branch, as indicated is installed via its install log file  
        self._remove_installed_files(pkg_to_turn_off_name, branch_to_turn_off_name, branch_installation_log_files, noise)

        # remove the installation log files (and subsequent empty dirs) just used
        self._remove_log_dirs(pkg_to_turn_off_name, branch_to_turn_off_name, pkg_logs_dir, branch_logs_dir, noise)

        # look recursively to see if the dirs in userbase are empty and removes those empty dirs.
        self._remove_empty_dirs_recursively(site.getuserbase(), noise)

        # rename the branch dir name (in the pkg_dir)
        if noise.verbose:
            print('Renaming the downloaded package {0} [{1}]...'.format(pkg_to_turn_off_name, branch_to_turn_off_name))
        pkg_dir = join(self.pkg_type_install_dir, pkg_to_turn_off_name)
        branch_dir = join(pkg_dir, branch_to_turn_off_name)

        branch_to_turn_off_renamed = '.__{0}'.format(branch_to_turn_off_name)
        branch_to_turn_off_renamed_dir = join(pkg_dir, branch_to_turn_off_renamed)
        os.rename(branch_dir, branch_to_turn_off_renamed_dir)

        # rename the branch in the installation_db
        #if noise.verbose:
            #print('Renaming the package {0} [{1}] in the {2} file...'.format(
                                                    #pkg_to_turn_off_name, branch_to_turn_off_name, installation_db))
        #handle_db_for_branch_renaming(self.pkg_type, pkg_to_turn_off_name, branch_to_turn_off_name, 
                                    #branch_to_turn_off_renamed, db_pname=installation_db_path)

        print('Successfully turned off {0} [{1}].'.format(pkg_to_turn_off_name, branch_to_turn_off_name))


    def _turn_on_check(self, pkg_type, pkg_to_turn_on_name, branch_to_turn_on, everything_already_installed, noise):
        all_branches_installed_for_pkgs_lang_ver = utils.branches_installed_for_given_pkgs_lang_ver(
                                                self.lang_cmd, 
                                                pkg_to_turn_on_name, everything_already_installed) 

        any_package_branch_on = [branch for branch in all_branches_installed_for_pkgs_lang_ver if not branch.startswith('.__')]

        for lang_installed, pkg_types_dict in everything_already_installed.items():
            if lang_installed == self.lang_cmd:
                for installed_pkg_type, pkgs_dict in pkg_types_dict.items():
                    for installed_pkg_name, branches_list in pkgs_dict.items(): 
                        if any_package_branch_on:
                            print("Cannot turn on {0} {1} [{2}] {3} because".format(pkg_type, pkg_to_turn_on_name, branch_to_turn_on, self.lang_cmd)) 
                            utils.when_not_quiet_mode("a version of {0} is already turned on for {1}.".format(pkg_to_turn_on_name, self.lang_cmd), noise.quiet) 
                            utils.when_not_quiet_mode("[Execute `{} list` to see currently turned on packages.]".format(name), noise.quiet)
                            return False
                        else:
                            return True


    def turn_on(self, pkg_to_turn_on_name, branch_to_turn_on_name, everything_already_installed, noise):
        self.branch_to_turn_on_renamed = branch_to_turn_on_renamed = branch_to_turn_on_name.lstrip('.__')  

        utils.when_not_quiet_mode('\nAttempting to turn on {0} [{1}]...'.format(pkg_to_turn_on_name, branch_to_turn_on_renamed), noise.quiet) 

        should_turn_back_on = self._turn_on_check(self.pkg_type, pkg_to_turn_on_name, branch_to_turn_on_renamed, everything_already_installed, noise)
        if should_turn_back_on: 

            # rename the branch dir name back to it's original name
            if noise.verbose:
                print('Renaming {0} {1}...'.format(pkg_to_turn_on_name, branch_to_turn_on_renamed))

            pkg_dir = join(self.pkg_type_install_dir, pkg_to_turn_on_name)

            branch_dir_raw_name = join(pkg_dir, branch_to_turn_on_name)
            branch_dir_renamed = join(pkg_dir, branch_to_turn_on_renamed)

            os.rename(branch_dir_raw_name, branch_dir_renamed)

            # rename the branch back to it's original name in the installation_db
            #if noise.verbose:
                #print('Renaming the package {0} [{1}] in the {2} file...'.format(
                                                    #pkg_to_turn_on_name, branch_to_turn_on_name, installation_db))
            #handle_db_for_branch_renaming(self.pkg_type, pkg_to_turn_on_name, branch_to_turn_on_name, 
                                        #branch_to_turn_on_renamed, db_pname=installation_db_path)

            # reinstall the branch files from the branch installation dir back into userbase
            if noise.verbose:
                print('Reinstalling {0} {1}...'.format(pkg_to_turn_on_name, branch_dir_renamed))
            Package.install(self, pkg_to_turn_on_name, noise, download_pkg=False)

            print('Successfully turned on {0} [{1}].'.format(pkg_to_turn_on_name, branch_to_turn_on_renamed))



class Git(Package):
    def __init__(self, lang_arg, pkg_type, install_dirs):
        self.repo_type = 'git'
        self.application_check_cmd = 'git --version'
        super(Git, self).__init__(lang_arg, pkg_type, install_dirs)
    
    def install(self, pkg_to_install, noise, **kwargs):
        self.download_url_cmd = '-b {0} {1}'
        #self.install_download_cmd = 'git clone --single-branch {0}' # maybe want "git clone --recursive" instead?
        self.install_download_cmd = 'git clone {0} {1}' 
        Package.install(self, pkg_to_install, noise, **kwargs)

    def update(self, lang_to_update, pkg_to_update, branch_to_update, noise):
        #self.update_cmd = 'git pull && git submodule update --init --recursive'
        self.update_cmd = 'git pull'
        self.up_to_date_output = 'Already up-to-date'
        Package.update(self, lang_to_update, pkg_to_update, branch_to_update, noise)


class Mercurial(Package):
    def __init__(self, lang_arg, pkg_type, install_dirs):
        self.repo_type = 'hg'
        self.application_check_cmd = 'hg --version'
        super(Mercurial, self).__init__(lang_arg, pkg_type, install_dirs)

    def install(self, pkg_to_install, noise, **kwargs):
        #self.download_url_cmd = '-r {0} {1}' # need to look more into these commands
        self.download_url_cmd = '-b {0} {1}'
        self.install_download_cmd = 'hg clone {0} {1}'
        Package.install(self, pkg_to_install, noise, **kwargs)

    def update(self, lang_to_update, pkg_to_update, branch_to_update, noise):
        self.update_cmd = 'hg pull -u'
        self.up_to_date_output = 'no changes found'
        Package.update(self, lang_to_update, pkg_to_update, branch_to_update, noise)


class Bazaar(Package):
    def __init__(self, lang_arg, pkg_type, install_dirs):
        self.repo_type = 'bzr'
        self.application_check_cmd = 'bzr --version'
        super(Bazaar, self).__init__(lang_arg, pkg_type, install_dirs)

    def install(self, pkg_to_install, noise, **kwargs):
        self.download_url_cmd =  '{0} {1}'  # i think this is how you install a specific branch (not sure though)
        self.install_download_cmd = 'bzr branch {0} {1}'    # bzr uses branch instead of clone
        Package.install(self, pkg_to_install, noise, **kwargs)

    def update(self, lang_to_update, pkg_to_update, branch_to_update, noise):
        self.update_cmd = 'bzr pull'
        self.up_to_date_output = 'No revisions or tags to pull.'
        Package.update(self, lang_to_update, pkg_to_update, branch_to_update, noise)


class RepoTypeCheck(Git, Mercurial, Bazaar):

    def install(self, pkg_to_install, noise, **kwargs):
        self.repo_type, pkg_to_install = pkg_to_install.split('+')
        if self.repo_type == 'hg':
            Mercurial.install(self, pkg_to_install, noise, **kwargs)
        elif self.repo_type == 'git':
            Git.install(self, pkg_to_install, noise, **kwargs)
        elif self.repo_type == 'bzr':
            Bazaar.install(self, pkg_to_install, noise, **kwargs)
        #elif <future_repo_type>:    # NOTE for other types of repos
            #<FutureRepoType.install(etc...)>
        else:   # should never hit this b/c it is(/should always be) covered in subclasses
            print("\nError installing {0}:".format(pkg_to_install))   
            print("Command to install packages needs to be specified as one of: {0}".format(self.allowed_repo_types))
            return

    def update(self, lang_to_update, pkg_to_update, branch_to_update, noise):
        pkg_install_dir = join(self.pkg_type_install_dir, pkg_to_update)
        branch_install_dir = join(pkg_install_dir, branch_to_update)
        contents_of_branch_install_dir = os.listdir(branch_install_dir) 

        if '.hg' in contents_of_branch_install_dir:
            Mercurial.update(self, lang_to_update, pkg_to_update, branch_to_update, noise)
        elif '.git' in contents_of_branch_install_dir:
            Git.update(self, lang_to_update, pkg_to_update, branch_to_update, noise)
        elif '.bzr' in contents_of_branch_install_dir:
            Bazaar.update(self, lang_to_update, pkg_to_update, branch_to_update, noise)
        #elif <future_repo_type>:    # NOTE for other types of repos
            #<FutureRepoType.update(etc...)>


class Github(Git):

    def install(self, pkg_to_install, noise, **kwargs):
        #self.repo_type = 'git'
        self.allowed_repo_types = ['git']
        is_repo_type_specified = pkg_to_install.split('+')
        if len(is_repo_type_specified) == 2:
            #print("\nNote: do not have to specify repo type for Github repos.") 
            pkg_to_install = is_repo_type_specified[-1]

        self.download_url = 'https://github.com/{0}.git'
        Git.install(self, pkg_to_install, noise, **kwargs)


class Gitorious(Git):
 
    def install(self, pkg_to_install, noise, **kwargs):
        #self.repo_type = 'git'
        self.allowed_repo_types = ['git']
        is_repo_type_specified = pkg_to_install.split('+')
        if len(is_repo_type_specified) == 2:
            #print("\nNote: do not have to specify repo type for Gitorious repos.") 
            pkg_to_install = is_repo_type_specified[-1]

        self.download_url = 'http://git.gitorious.org/{0}.git'
        Git.install(self, pkg_to_install, noise, **kwargs)


class Bitbucket(RepoTypeCheck):

    def install(self, pkg_to_install, noise, **kwargs):
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
        RepoTypeCheck.install(self, pkg_to_install, noise, **kwargs)


class Local_Repo(RepoTypeCheck):
 
    def install(self, pkg_to_install, noise, **kwargs):
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
        RepoTypeCheck.install(self, pkg_to_install, noise, **kwargs) 


# TODO to add in ability to use urls for ssh access and the like.
#class Remote_Repo(RepoTypeCheck):

    #def install(self, pkg_to_install, noise):
        #self.allowed_repo_types = ['git', 'hg', 'bzr'] # maybe 'svn'?


class Stable(Package):
    pass
