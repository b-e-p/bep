
#----------------------------------------------------------------
# Author: Jason Gors <jasonDOTgorsATgmail>
# Creation Date: 09-20-2013
# Purpose: this is the point of call from the bep script.
# License: BSD
#----------------------------------------------------------------

import sys

pyversion = float(sys.version[0:3])
if pyversion < 2.7:
    raise SystemExit("Requires Python >= 2.7; Current version is %s" % pyversion)


def _run_bep():
    from Bep.run import main
    main()

