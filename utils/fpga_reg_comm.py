#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Dec 09, 2019 at 02:00 AM -0500

import sys

sys.path.insert(0, '..')

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read
from nanoDAQ.gbtclient.fpga_reg import mem_mon_fiber_read, mem_mon_fiber_write
from nanoDAQ.gbtclient.fpga_reg import mem_mon_options_read, \
    mem_mon_options_write
from nanoDAQ.phase import print_elink_table, alternating_color


read = mem_mon_read
fiber_r = mem_mon_fiber_read
fiber_w = mem_mon_fiber_write
opts_r = mem_mon_options_read
opts_w = mem_mon_options_write
tab = lambda x: print_elink_table(x, style=alternating_color)
