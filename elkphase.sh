#!/bin/sh
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Jan 17, 2020 at 01:51 AM -0500

PHASE=$1

for elk_channel in 11 10 9 8 7 6 5 4 3 2 1; do
    # NOTE: "${@:2}" pass-thru all arguments except the first
    ./dcbutil.py elk_phase ${elk_channel} ${PHASE} "${@:2}"
done
