#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Dec 09, 2019 at 12:03 AM -0500

import sys
import pydim

from platform import node

sys.path.insert(0, '..')

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read
from nanoDAQ.phase import print_elink_table, alternating_color


read = mem_mon_read
tab = lambda x: print_elink_table(x, style=alternating_color)


PREFIX = 'Gbt/{}/'.format(node())


def cmnd(name, cmd, dev='TELL40_Dev1_0.top_tell40'):
    pydim.dic_sync_cmnd_service(PREFIX+'CmndOperation/'+dev+'.'+name, cmd)


def srvc(name, srvc='SrvcReadings/', dev='TELL40_Dev1_0.top_tell40'):
    return pydim.dic_sync_info_service(PREFIX+srvc+dev+'.'+name)
