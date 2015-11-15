#!/usr/bin/python

#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 09-18-2013
# Purpose:  help commands.
#----------------------------------------------------------------


#subparser_use = '''
#[ Command specific help info ]
#'''


epilog_use = '''
See command specific help by issuing a trailing `-h` after the command:
(eg. `%(prog)s [command] -h`)
'''


verbose_use = '''
show all output during specified command processes.
'''

quiet_use = '''
show minimal output during specified command processes.
'''

lang_use = '''
specify a language version to use.
(default is system default:  %(default)s)
'''


all_use = '''
can use to either update|remove|turn_off all installed
packages at once.
'''


list_use = '''
Lists all installed packages and whether each package
version is turned on or off.
'''

list_sub_use = '''
List does not take any arguments, and when called, it lists
all installed packages and whether each is turned on or off.
'''


install_use = '''
Installs specified package(s).
Can be used to either install one specific package
at a time or to install several packages at once as
specified in the {} file.

'''

install_sub_use = '''

Installing a single package.
-----------------------------------------------------
(Note, specifying a branch is optional; if a branch/version
is not given, then the most current(/master/default)
branch is installed; also, repo_type needs only to be
specified if it is not obvious given the pkg_type:
github could only be git, but bitbucket would need
to be specified, as it could be either git or hg)
  `%(prog)s pkg_type pkg_name [repo_type] [branch]`

  eg.  %(prog)s github ipython/ipython
  eg.  %(prog)s github pydata/pandas -b some_branch
  eg.  %(prog)s bitbucket mchaput/whoosh hg
'''


packages_file_use = '''
Installing several packages.
-----------------------------------------------------
installs all packages specified in the {} file.
  eg. %(prog)s packages
'''



class cmd_help(object):

    update_use = '''
Updates specified package(s).
Can pass an argument to either update a specific
package or to update `--all` (turned on) packages.
'''

    update_sub_use = '''

(note, update ignores turned off packages)

To see the exact syntax of how to update a package,
just pass an installed package name to the update
command; the command can be run from there as well.
-----------------------------------------------------
  `%(prog)s pkg_name`

  eg.  %(prog)s ipython


Updating a single package.
-----------------------------------------------------
  `%(prog)s pkg_type pkg_name --branch|-b branch_name`

  eg.  %(prog)s github ipython -b master
  eg.  %(prog)s bitbucket some_pkg_name -b default

  And for a package not using the system default
  language version:
  eg.  {name} -l python3.3 update github ipython -b master



Updating several packages.
-----------------------------------------------------
`--all`: all turned on packages will be updated,

  eg.  %(prog)s --all
'''



    remove_use = '''
Removes specified package(s).
Can pass an argument to either remove a specific
package or to remove `--all` installed packages.
'''
#or to only remove all `turned_off` packages.

    remove_sub_use = '''

To see the exact syntax of how to remove a package,
just pass an installed package name to the remove
command; the command can be run from there as well.
-----------------------------------------------------
  `%(prog)s pkg_name`

  eg.  %(prog)s ipython


Removal of a single package.
-----------------------------------------------------
  `%(prog)s pkg_type pkg_name --branch|-b branch_name`

  eg.  %(prog)s github ipython -b master
  eg.  %(prog)s bitbucket whoosh -b default

  And for a package not using the system default
  language version:
  eg.  {name} -l python3.3 remove github ipython -b master


Removal of several packages.
-----------------------------------------------------
`--all`: all installed packages will be removed,

    eg.  %(prog)s --all

'''
#`turned_off`: all turned off packages will be removed,
    #`%(prog)s turned_off turned_off`

    #eg.  %(prog)s turned_off


    turn_off_use = '''
Turns off specified package(s).
Can pass an argument to either turn off a specific
package or to turn off `--all` installed packages.
What this does is that it makes the given
package(s) inactive so that they are hidden from the
environment.  This is useful for a few reasons, see
`%(prog)s turn_off -h` for more information.
'''

    turn_off_sub_use = '''

Turning off packages is useful because:
1. It makes it so that several versions of the
   same package can be installed (from the same
   or different pkg_type or version of the language),
   which can then be easily switched between -- with
   only one version of a given package capable of
   being turned on at any given time for a language
   version;
2. Thus, if all installed versions are turned off,
   then that same package installed at the system
   level (if there is one) can be accessed without
   having to remove the package;
3. And by turning off a package, it means that it
   will then not have to be re-downloaded and re-
   installed if wanting to use it again later (by
   later using `turn_on` to reactivate the package),
   which could potentially save much time building
   and installing a package.


To see the exact syntax of how to turn off a package,
just pass an installed package name to the turn_off
command; the command can be run from there as well.
-----------------------------------------------------
  `%(prog)s pkg_name`

  eg.  %(prog)s ipython


Turning off a single package.
-----------------------------------------------------

  `%(prog)s pkg_type pkg_name --branch|-b branch_name`

  eg.  %(prog)s github ipython -b master
  eg.  %(prog)s bitbucket some_pkg_name -b default

  And for a package not using the system default
  language version:
  eg.  {name} -l python3.3 turn_off github ipython -b master


Turning off several packages.
-----------------------------------------------------
`--all`: all installed packages will be turned off.

    eg.  %(prog)s --all
'''



    turn_on_use = '''
Turns on a specified package.
Can pass an argument to turn on a specific
package that is currently turned off.
'''

    turn_on_sub_use = '''

If there are packages that are turned off, then this will
reactivate them so that they can be seen once again by the
environment for use.  Note, only one version of a specific
package can be turned on at any given time for a specific
language version.


To see the exact syntax of how to turn on a package,
just pass an installed package name to the turn_on
command; the command can be run from there as well.
-----------------------------------------------------
  `%(prog)s pkg_name`

  eg.  %(prog)s ipython


Turning on a single package.
-----------------------------------------------------
  `%(prog)s pkg_type pkg_name --branch|-b branch_name`

  eg.  %(prog)s github ipython -b master
  eg.  %(prog)s bitbucket some_pkg_name -b default

  And for a package not using the system default
  language version:
  eg.  {name} -l python3.3 update github ipython -b master

'''
