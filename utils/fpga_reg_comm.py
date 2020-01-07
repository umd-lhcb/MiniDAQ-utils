#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Jan 07, 2020 at 01:15 AM -0500

import sys

sys.path.insert(0, '..')

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe
from nanoDAQ.gbtclient.fpga_reg import mem_mon_fiber_read_safe, \
    mem_mon_fiber_write_safe
from nanoDAQ.gbtclient.fpga_reg import mem_mon_options_read_safe, \
    mem_mon_options_write_safe
from nanoDAQ.elink import print_elink_table


read    = mem_mon_read_safe
fiber_r = mem_mon_fiber_read_safe
fiber_w = mem_mon_fiber_write_safe
opts_r  = mem_mon_options_read_safe
opts_w  = mem_mon_options_write_safe
tab     = lambda x: print_elink_table(x)
