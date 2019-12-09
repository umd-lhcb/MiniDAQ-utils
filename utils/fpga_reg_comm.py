#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Sun Dec 08, 2019 at 09:24 PM -0500

import sys
import pydim

from platform import node

sys.path.insert(0, '..')

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read


read = mem_mon_read


PREFIX = 'Gbt/{}/'.format(node())


def cmnd(name, cmd, dev='TELL40_Dev1_0.top_tell40'):
    pydim.dic_sync_cmnd_service(PREFIX+'CmndOperation/'+dev+'.'+name, cmd)


def srvc(name, srvc='SrvcReadings/', dev='TELL40_Dev1_0.top_tell40'):
    return pydim.dic_sync_info_service(PREFIX+srvc+dev+'.'+name)
