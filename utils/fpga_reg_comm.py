#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Sun Dec 08, 2019 at 03:10 AM -0500

import sys
import pydim

from platform import node

sys.path.insert(0, '..')

from nanoDAQ.utils import hex_pad


PREFIX = 'Gbt/{}/'.format(node())


def cmnd(name, cmd, dev='TELL40_Dev1_0.top_tell40'):
    pydim.dic_sync_cmnd_service(PREFIX+'CmndOperation/'+dev+'.'+name, cmd)


def srvc(name, srvc='SrvcReadings/', dev='TELL40_Dev1_0.top_tell40'):
    return pydim.dic_sync_info_service(PREFIX+srvc+dev+'.'+name)


def decode(ret):
    if isinstance(ret[1], bytes):
        return [hex_pad(i) for i in ret[1]]
    elif isinstance(ret[1], str):
        return [hex_pad(ord(i)) for i in ret[1]]


def chunks(lst, size=16):
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def dataframe_format(df):
    tmp_lst = map(''.join, chunks(df, 4))
    return ' '.join(tmp_lst)
