#!/usr/bin/python

"""
#----------------------------------------------------------------
Author: Jason Gors <jasonDOTgorsATgmail>
Creation Date: 09-18-2013
Purpose:  help commands.
#----------------------------------------------------------------
"""


subparser_use = '''
[ Subcommand specific help info ]
'''


epilog_use = '''
See command specific help by issuing a trailing `-h` after the command: 
(eg. `%(prog)s [command] -h`)
'''


verbose_use = '''
show all output during the command processes.
'''

quiet_use = '''
show minimal output during the command processes.
'''

lang_use = '''
to specify a language to use.
'''


list_use = '''
Lists all installed packages and whether each package's branch is turned on or off.
'''

list_sub_use = '''
List does not take any arguments, and when called by itself, it lists  
all installed packages; however, list can be specified after the  
optional language arg to show only packages installed for that language.
'''


install_use = '''
Installs specified package(s). 
Can either pass an argument to install a specific 
package at the command line, or if no argument is
given to the install command, then all packages  
specified in the {} file will be installed.  
'''

install_sub_use = '''

(default: %(default)s)

Installing several packages. 
-----------------------------------------------------
installs packages specified in the {} file
(don't pass any arguments to the install command)
    eg. %(prog)s


Installing a single package.  
-----------------------------------------------------
(note, specifying a branch is optional; if a branch 
is not given, then the master branch is installed)
    `bep --language=lang install pkg_type=repo_type+pkg_name[^optional_branch]`

    eg.  bep --language=python install github=git+ipython/ipython
    eg.  bep --language=python install github=git+ipython/ipython^branch_name
'''


update_use = '''
Updates specified package(s).  
Can pass an argument to either update a specific 
package, or to update `ALL` turned on packages (or 
`ALL` turned on packages for a given language). 
'''

update_sub_use = '''

(update ignores turned off packages)

To see the exact syntax of how to update a package, just  
pass the installed package name to the update command.
-----------------------------------------------------
    `%(prog)s pkg_name`

    eg.  %(prog)s ipython


Updating a single package. 
-----------------------------------------------------
    `bep --language=lang update pkg_type=pkg_name[^optional_branch]`

    eg.  bep --language=python update github=ipython


Updating several packages.
-----------------------------------------------------
`ALL`: all packages specified will be updated,
    `bep [--language=lang] update ALL`

    eg.  bep update ALL
    eg.  bep --language=python2.6 update ALL
'''



remove_use = '''
Removes specified package(s).
Can pass an argument to either remove a specific 
package; to remove `ALL` installed packages (or 
`ALL` installed packages for a given language); 
or to remove all `turned_off` packages (or all 
`turned_off` packages for a given language).
'''

remove_sub_use = '''

To see the exact syntax of how to remove a package, 
just pass the package name to the remove command.
-----------------------------------------------------
    `%(prog)s pkg_name`

    eg.  %(prog)s ipython


Removal of a single package.
-----------------------------------------------------
    `bep --language=lang remove pkg_type=pkg_name[^optional_branch]`

    eg.  bep --language=python remove github=ipython


Removal of several packages.
-----------------------------------------------------
`ALL`: all installed packages will be removed,
    `bep [--language=lang] remove ALL`

    eg.  bep remove ALL
    eg.  bep --language=python2.6 remove ALL


`turned_off`: all turned off packages will be removed, 
    `bep [--language=lang] remove turned_off`

    eg.  bep remove turned_off
    eg.  bep --language=python2.6 remove turned_off
'''


turn_off_use = '''
Turns off specified package(s).  
Can pass an argument to either turn off a specific package, 
or to turn off `ALL` installed packages (or `ALL`  packages 
for a given language). What this does is that it makes the 
package(s) inactive so that they are hidden from the 
environment.  This is useful for a few reasons, see 
`%(prog)s turn_off -h` for more information.
'''

turn_off_sub_use = '''

Turning off packages is useful because:
1. It makes it so that several versions of the 
    same package can be installed (from the same 
    or different pkg_type or version of a language), 
    which can then be easily switched between -- with 
    only one version of a given package capable of 
    being turned on at any given time for a language; 
2. Thus, if all installed versions are turned off, 
    then that same package installed at the system 
    level (if there is one) can be accessed without 
    having to remove the package; 
3. And by turning off a package, it means that it 
    will then not have to be re-downloaded and re-
    installed if wanting to use it again later (by 
    later using `turn_on`), which could potentially 
    save much time installing and building a package.


To see the exact syntax of how to turn off a package, 
just pass the package name to the turn_off command:
-----------------------------------------------------
    `%(prog)s pkg_name`

    eg.  %(prog)s ipython


Turning off a single package.
-----------------------------------------------------
    `bep --language=lang turn_off pkg_type=pkg_name[^optional_branch]`

    eg.  bep --language=python turn_off github=ipython


Turning off several packages.
-----------------------------------------------------
`ALL`: all installed packages will be turned off,
    `bep [--language=lang] turn_off ALL`

    eg.  bep turn_off ALL
    eg.  bep --language=python2.6 turn_off ALL
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
just pass the package name to the turn_on command.
-----------------------------------------------------
    `%(prog)s pkg_name`

    eg.  %(prog)s ipython


Turning on a single package.
-----------------------------------------------------
    `bep --language=lang turn_on pkg_type=pkg_name[^optional_branch]`

    eg.  bep --language=python turn_on github=ipython

'''
