#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Dec 09, 2019 at 12:53 AM -0500

import sys

sys.path.insert(0, '..')

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read, mem_mon_fiber
from nanoDAQ.phase import print_elink_table, alternating_color


read = mem_mon_read
fiber = mem_mon_fiber
tab = lambda x: print_elink_table(x, style=alternating_color)
