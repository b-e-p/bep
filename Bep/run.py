#! /usr/bin/env python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 07-30-2013
# Purpose: this is where the program is called into action.
#----------------------------------------------------------------

import argparse
import os
from os.path import join
import sys
import copy
from collections import OrderedDict

from Bep.core import usage
from Bep.core.release_info import __version__, name
from Bep.core import utils
from Bep.cmds import install, list_packages, remove_packages, turn_off, turn_on, update_packages




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

repo_choices = ['github', 'bitbucket', 'local'] # 'remote'
other_choices = ['packages'] # 'stable'
possible_choices = repo_choices + other_choices



def main(): # needs to be done as a main func for setuptools to work correctly in creating an executable
    # for the approach i am taking here using nested subparsers:
    # https://mail.python.org/pipermail/python-list/2010-August/585617.html

    # nargs options:
    # (default): by not specifying nargs at all, you just get a string of 1 item
    # = N   where N is some specified number of args
    # = '?' makes a string of one item, and if no args are given, then default is used.
    # = '*' makes a list of all args passed after command and if no args given, then default is used.
    # = '+' makes list of all args passed after command, but requires at least one arg

    top_parser = argparse.ArgumentParser(description=name.upper(),
                            formatter_class=argparse.RawDescriptionHelpFormatter,
                            #formatter_class=argparse.RawTextHelpFormatter,
                            #add_help=False,
                            epilog=usage.epilog_use)

    #################################
    ### this goes at the top level
    top_parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    top_parser.add_argument('-l', '--language', nargs='?', default='python', help=usage.lang_use)

    group = top_parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", help=usage.verbose_use)
    group.add_argument("-q", "--quiet", action="store_true", help=usage.quiet_use)
    #################################


    def check_for_all_error(cmd_arg):
        if cmd_arg in ['all', 'All', 'ALL', '--All', '--ALL']:
            raise SystemExit("\nError: Did you mean to specifiy --all instead?")


    # If --all is passed in:
    # Skip stuff below if '--all' is specified w/ one of these accepted cmds
    # (this is some seriously hacky brute force shit!)
    build_up_subparsers = True
    additional_args = []
    cmds_that_accept_all_arg = ['update', 'remove', 'turn_off']
    for cmd in cmds_that_accept_all_arg:
        if cmd in sys.argv:
            for i in sys.argv:  # test for misspecified '--all' command
                check_for_all_error(i)
            if '--all' in sys.argv:
                #print(sys.argv)
                build_up_subparsers = False
                                                                            # TODO add help page for all
                top_parser.add_argument('--all', action='store_true', help=usage.all_use) #metavar="arg")
                args = top_parser.parse_known_args()
                args, additional_args = args
                if len(additional_args) > 1:    # this makes it so that it could only be len(additional_args)==1
                    error_all_arg = "--all can only be called with one of the following args:\n\t"
                    error_all_arg = error_all_arg + '{update, remove, turn_off}'
                    top_parser.error(error_all_arg)
                #else:
                    #additional_args = additional_args[0]


    # To display how to run a command:
    # look at all pkgs and check that passed in package name is one that's already installed
    everything_already_installed = utils.all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir)
    any_of_this_pkg_already_installed = lambda pkg_to_process: utils.lang_and_pkg_type_and_pkg_and_branches_tuple(
                                                                        pkg_to_process, everything_already_installed)
    cmds_that_can_display_how_to = cmds_that_accept_all_arg + ['turn_on']
    for cmd in cmds_that_can_display_how_to:    # everything except install i think
        if (cmd in sys.argv) and ('--all' not in sys.argv):
            if ('-h' not in sys.argv) and ('--help' not in sys.argv):
                args = top_parser.parse_known_args()
                args, additional_args = args
                if len(additional_args) == 2:
                    additional_args_copy = copy.copy(additional_args)
                    additional_args_copy.remove(cmd) # 2 things in here, one equal to cmd, the other is what we want to see if it's alreay installed
                    potential_pkg_to_proc = additional_args_copy[0]

                    #print any_of_this_pkg_already_installed(potential_pkg_to_proc)
                    if any_of_this_pkg_already_installed(potential_pkg_to_proc):
                        # should i make a function call out of this instead of relying on the command to be handled below?
                        print(" **** This is how to {} {} ****".format(cmd, potential_pkg_to_proc))
                        build_up_subparsers = False
                    elif potential_pkg_to_proc not in possible_choices:   # else if the other arg/package name passed in is not a pkg_already_installed (& not one of the next possible cmd options)
                        #print an error say that whatever is passed in cannot be updated/turned_on/etc
                        #b/c it's not currently installed.
                        error_msg = "cannot {} {}: not a currently installed package.\n".format(cmd, potential_pkg_to_proc)
                        error_msg = error_msg + "[Execute `{} list` to see installed packages.]".format(name)
                        top_parser.error(error_msg)
                    #else:   # want this instead b/c otherwise the above hides the help pages
                        #additional_args = []     # set back to empty to avoid the flag at the end of argparse stuff
                #else:
                    #error_msg = "An already installed package name must be passed in with {}".format(cmd)
                    #top_parser.error(error_msg)
                else:
                    additional_args = []     # set back to empty to avoid the flag at the end of argparse stuff


    if build_up_subparsers:
        top_subparser = top_parser.add_subparsers(title='Commands',
                                        description='[ These are the commands that can be passed to %(prog)s ]',
                                        #help=usage.subparser_use)
                                        help='[ Command specific help info ]')
        ### create parser for the "list" command
        # maybe make it so that it can list all branches installed for a specific pkg,
        parser_list = top_subparser.add_parser('list', help=usage.list_use)
        parser_list.add_argument('list_arg', action="store_true", help=usage.list_sub_use) #metavar="arg")


        class CheckIfCanBeInstalled(argparse.Action):
            ''' makes sure a repo to install has both a user_name and repo_name:
                    eg. ipython/ipython
                or is an actual path to a repo on the local filesystem'''

            def __call__(self, parser, namespace, arg_value, option_string=None):
                pkg_type = parser.prog.split(' ')[-1]
                if utils.check_if_valid_pkg_to_install(arg_value, pkg_type):
                    setattr(namespace, self.dest, arg_value)
                else:
                    if pkg_type == 'local':
                        error_msg = "\n\tIs not a path that exists on local filesystem."
                        raise parser.error(arg_value + error_msg)
                    else:
                        error_msg = '\nneed to make sure a username and repo_name are specified, like so:\n\tusername/repo_name'
                        raise parser.error(arg_value + error_msg)


        ##################################################
        cmd_help = vars(usage.cmd_help)
        for cmd in ['install', 'update', 'remove', 'turn_off', 'turn_on']:
            if cmd == 'install':
                install_parser = top_subparser.add_parser(cmd, help=usage.install_use.format(packages_file),
                                                          formatter_class=argparse.RawTextHelpFormatter)
                install_parser.set_defaults(top_subparser=cmd)
                install_subparser = install_parser.add_subparsers(dest='pkg_type', help=usage.install_sub_use.format(packages_file))
                for c in repo_choices:
                    pkg_type_to_install = install_subparser.add_parser(c)
                    # pkg_type_to_install.set_defaults(pkg_type_to_install=c) # is the same as 'pkg_type' dest above

                    pkg_type_to_install.add_argument('pkg_to_install',   # like ipython/ipython
                                                     action=CheckIfCanBeInstalled)   # actions here to make sure it's legit

                    # local repos don't get to have a branch specified; a branch would need to be checked out first, then installed.
                    #if c != 'local':
                        #pkg_type_to_install.add_argument('-b', '--branch', dest='branch', default=None)#, action=CheckBranch)    # the branch bit is filled out below

                    if c == 'github':
                        pkg_type_to_install.add_argument('repo_type', default='git', nargs='?')

                    elif c == 'bitbucket':
                        pkg_type_to_install.add_argument('repo_type', choices=['git', 'hg'])

                    # elif c == 'local':    # just get the type of repo from the local filesystem so it doesn't have to be specified
                        # pkg_type_to_install.add_argument('repo_type', choices=['git', 'hg', 'bzr'])

                    #elif c == 'remote':    # TODO not implemented but would be specified like so
                        #pkg_type_to_install.add_argument('repo_type', choices=['git', 'hg', 'bzr'])

                    pkg_type_to_install.add_argument('-b', '--branch', dest='branch', default=None)#, action=CheckBranch)    # the branch bit is filled out below

                for c in other_choices:
                    if c == 'packages':
                        pkg_type_to_install = install_subparser.add_parser(c, help=usage.packages_file_use.format(packages_file))

                    #elif c == 'stable': # TODO not implemented
                        #pkg_type_to_install = install_subparser.add_parser(c)
                        #pkg_type_to_install.add_argument('pkg_to_install')  # like ipython
                        ##pkg_type_to_install.add_argument('--pversion')      # TODO like 1.2.1 (add this in later to install different version of a stable pkg)

                # NOTE this seems like a better way to go in the future:
                # install_parser.set_defaults(func=run_install)
                # then run_install would be defined to run the install process (rather than having the conditionals below)
                # def run_install(args):
                #   install_arg = args.install_arg  # would be a list of pkgs or a string of the packages file
                #   ...process the install_arg to decide what to install
                #   ...then do the install
                ##################################################
            else:
                subparser_parser = top_subparser.add_parser(cmd, help=cmd_help['{}_use'.format(cmd)],
                                                            formatter_class=argparse.RawTextHelpFormatter)
                subparser_parser.set_defaults(top_subparser=cmd)

                ### didn't work, not sure why yet
                #all_dest = '{}_ALL'.format(cmd)
                #subparser_parser.add_argument('--all',
                                                ##help=usage.remove_sub_use.format(name=name),    # FIXME not sure why this wouldn't work
                                                ##action=CheckIfALL, action='store_true')

                #cur_args = vars(top_parser.parse_args())
                #print(cur_args)
                #if 'all' in cur_args:
                    #if cur_args['all']:
                        #break
                this_cmds_help = cmd_help['{}_sub_use'.format(cmd)].format(name=name)
                subparsers_subparser = subparser_parser.add_subparsers(dest='pkg_type', help=this_cmds_help)

                for c in repo_choices:
                    pkg_type_to_proc = subparsers_subparser.add_parser(c)
                    pkg_type_to_proc.add_argument('pkg_to_{}'.format(cmd))   # like ipython
                    pkg_type_to_proc.add_argument('-b', '--branch', dest='branch', default=None)  # needs to be specified in script (for installs though it use default name if not specified)

                #for c in other_choices: #TODO
                    ##if c == 'packages':    # packages args only used for installs
                        ##pkg_type_to_proc = subparsers_subparser.add_parser(c)
                    #if c == 'stable':
                        #pkg_type_to_proc = subparsers_subparser.add_parser(c)
                        #pkg_type_to_proc.add_argument('pkg_to_{}'.format(cmd))  # like ipython
                        #pkg_type_to_proc.add_argument('--pversion', help='package version')      # like 1.2.1 (default should be the newest, but can specify older ones)
            ##################################################



        args = top_parser.parse_args()

        # handle branches here
        if ('top_subparser' in args) and (args.top_subparser == 'install'):
            if ('branch' in args) and (args.branch == None):
                if args.pkg_type == 'local':    # for local, grab the currently checked out branch from the repo and set that as the branch to install
                    branch, repo_type = utils.get_checked_out_local_branch(args.pkg_to_install)
                    args.repo_type = repo_type
                else:
                    branch = utils.get_default_branch(args.repo_type)
                args.branch = branch
            elif ('branch' in args) and (args.branch != None):
                if args.pkg_type == 'local':    # for local, don't allow branch to be specified; just use currently checked out branch
                    error_msg = "for `local` packages a branch cannot be specified;\n"
                    error_msg = error_msg + "check out the desired branch from the repo itself, then install."
                    raise top_parser.error(error_msg)
        elif ('top_subparser' in args) and (args.top_subparser != 'install'):
            if ('branch' in args) and (args.branch == None):
                error_msg = 'need to make sure a branch is specified;\n'
                error_msg = error_msg + "[Execute `{} list` to see installed packages and branches.]".format(name)
                raise top_parser.error(error_msg)


    class noise(object):
        verbose = args.verbose
        quiet = args.quiet


    """
    # REMOVE LATER...this just shows what we're dealing with here
    print('##########################################################')
    print(args)
    if additional_args:
        print(additional_args)
    print('##########################################################')
    #raise SystemExit
    """

    #--------------------------------------------------------------------------------------------------------------

    if noise.quiet:
        print('-'*60)



    #######################################################################################################################
    #### install pkg(s)
    kwargs = dict(packages_file=packages_file, packages_file_path=packages_file_path,
                 noise=noise, install_dirs=install_dirs, installed_pkgs_dir=installed_pkgs_dir)

    if ('top_subparser' in args) and (args.top_subparser == 'install'):
        any_pkgs_processed = install.install_cmd(args, **kwargs)
    #######################################################################################################################



    #######################################################################################################################
    #### if nothting is installed, then don't continue on to other commands (since they only process currenly installed stuff)
    everything_already_installed = utils.all_pkgs_and_branches_for_all_pkg_types_already_installed(installed_pkgs_dir)
    if not everything_already_installed:
        raise SystemExit('\nNo packages installed.')
    #######################################################################################################################



    #######################################################################################################################
    #### list installed pkg(s) (by each package type)
    elif 'list_arg' in args:
        list_packages.list_cmd(everything_already_installed, noise)
    #######################################################################################################################



    #######################################################################################################################
    # for everything else (update, remove, turn_on/off)
    #elif args:
    #elif ((('top_subparser' in args) and (args.top_subparser in ['update', 'remove', 'turn_on', 'turn_off'])) or
         #(('update' in additional_args) or ('remove' in additional_args) or ('turn_off' in additional_args) or
          #('turn_on' in additional_args))):
    else:   # FIXME not sure this is as good as it could be by just using else instead of something more specific

        actions_to_take = {}
        #top_level_any_pkgs_processed = False
        for lang_dir_name, pkg_type_dict in everything_already_installed.items():
            for pkg_type, pkgs_and_branches in pkg_type_dict.items():
                any_pkgs_processed = False
                #if pkgs_and_branches:  # don't think i need this

                pkgs_status = utils.pkgs_and_branches_for_pkg_type_status(pkgs_and_branches)
                pkgs_and_branches_on = pkgs_status['pkg_branches_on']
                pkgs_and_branches_off = pkgs_status['pkg_branches_off']

                kwargs = dict(lang_dir_name=lang_dir_name, pkg_type=pkg_type, noise=noise, install_dirs=install_dirs,
                            pkgs_and_branches_on=pkgs_and_branches_on, pkgs_and_branches_off=pkgs_and_branches_off,
                            additional_args=additional_args, everything_already_installed=everything_already_installed)


                if ('pkg_to_update' in args) or ('update' in additional_args):
                    any_pkgs_processed = update_packages.update_cmd(args, **kwargs)

                elif ('pkg_to_remove' in args) or ('remove' in additional_args):
                    any_pkgs_processed = remove_packages.remove_cmd(args, **kwargs)

                elif ('pkg_to_turn_off' in args) or ('turn_off' in additional_args):
                    any_pkgs_processed = turn_off.turn_off_cmd(args, **kwargs)

                elif ('pkg_to_turn_on' in args) or ('turn_on' in additional_args):
                    any_pkgs_processed = turn_on.turn_on_cmd(args, **kwargs)


                if any_pkgs_processed:
                    #top_level_any_pkgs_processed = True #+= 1
                    if type(any_pkgs_processed) == dict:    # it will be a dict when a pkg didn't actually get processed, but has commands to get processed
                        actions_to_take.update(any_pkgs_processed)

        #if not top_level_any_pkgs_processed: # NOTE KEEP for now, but i don't think this will ever get hit?
            #utils.when_not_quiet_mode('\n[ No action performed ]'.format(pkg_type), noise.quiet)


        if actions_to_take:

            if len(actions_to_take) == 1:
                alert, cmd = actions_to_take.items()[0]
                option = '\n* {}\n{}\n'.format(alert, cmd)
                print(option)

                if not (cmd.startswith('****') and cmd.endswith('****')):

                    print('-'*60)
                    msg = "The above version is installed, would you like to run the\ncommand [y/N]? "
                    response = raw_input(msg)
                    if response:
                        response = response.lower()
                        if response in ['y', 'yes']:
                            utils.cmd_output(cmd)
                        elif response in ['n', 'no']:
                            print("\nBye then.")
                        else:
                            raise SystemExit("\nError: {}: not valid input".format(response))
                    else:
                        print("\nOk, bye then.")


            elif len(actions_to_take) > 1:

                actions_to_take_with_num_keys = {}  # takes the alert, cmd (key, val) pairs from actions_to_take and makes them as a value tuple, w/ a num as each pair's key.
                for num, alert_key in enumerate(actions_to_take, start=1): # actions_to_take is a dict with alert, cmd (key, val) pairs
                    actions_to_take_with_num_keys[num] = (alert_key, actions_to_take[alert_key])
                actions_to_take_with_num_keys = OrderedDict(sorted(actions_to_take_with_num_keys.items(), key=lambda t: t[0]))  # sorted by key (which are nums)

                for num_key, alert_and_cmd_tuple_val in actions_to_take_with_num_keys.items():
                    if num_key == 1:
                        print('')
                    alert, cmd =  alert_and_cmd_tuple_val
                    option = '{}. {}\n{}\n'.format(num_key, alert, cmd)
                    print(option)

                print('-'*60)
                msg = "The versions above are installed.  If you'd like to run the command\n"
                msg = msg + "for an item, enter the number (if not, then just hit enter to exit). "
                response = raw_input(msg)
                if response:
                    try:
                        response = int(response)
                    except ValueError:
                        raise SystemExit("\nError: invalid response: {}".format(response))
                    if response in range(1, len(actions_to_take_with_num_keys)+1):
                        #print response # now run the command
                        # Could either 1. open a subprocess and run from the command line -- easy way
                        # or 2. try to pass back into the the command that got us here -- better way

                        # Number 2 would involve something like this with updating the kwargs:
                        #kwargs = dict(lang_dir_name=lang_dir_name, pkg_type=pkg_type, noise=noise, install_dirs=install_dirs,
                                    #pkgs_and_branches_on=pkgs_and_branches_on, pkgs_and_branches_off=pkgs_and_branches_off,
                                    #additional_args=additional_args, everything_already_installed=everything_already_installed)
                        #actions.update_action(args, **kwargs)

                        # Doing number 1 above, just to get it working, though 2 would probably be better in long run.
                        cmd = actions_to_take_with_num_keys[response][1]    # this gets the command from the alert, cmd tuple
                        if (cmd.startswith('****') and cmd.endswith('****')):
                            print("\nNo command to process,\n{}".format(cmd))
                        else:
                            utils.cmd_output(cmd)
                    else:
                        raise SystemExit("\nError: invalid response: {}".format(response))
                else:
                    print("\nOk, bye then.")
