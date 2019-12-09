#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Sun Dec 08, 2019 at 09:22 PM -0500

import pydim

from .common import GBT_PREF, GBT_SERV, TELL40
from .common import errs_factory, dim_cmd_err, dim_dic_err

from ..utils import hex_pad, chunks
from ..phase import elink_parser


#############
# Constants #
#############

FPGA_REG_ERR_CODE = errs_factory()

FPGA_REG_OP_MODE = {
    'write':     0,
    'read':      1,
    'writeread': 2,
}


#####################
# Memory monitoring #
#####################

def mem_mon_decode(mem):
    if isinstance(mem, bytes):
        return [hex_pad(m) for m in mem]
    elif isinstance(mem, str):
        return [hex_pad(ord(m)) for m in mem]


def mem_mon_regulator(tp):
    mem = mem_mon_decode(tp[1])
    elink_df_lst = list(map(elink_parser, chunks(mem)))
    return (tp[0], elink_df_lst)


def mem_mon_read(tell40=TELL40, regulator=mem_mon_regulator):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndGPIOOperation/{}.top_tell40_monitoring.memory'.format(
            GBT_PREF, GBT_SERV),
        (FPGA_REG_OP_MODE['read'], '1'), 'C:1;C')
    dim_cmd_err(ret)

    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcReadings/{}.top_tell40_monitoring.memory'.format(
            GBT_PREF, GBT_SERV), 'I:1;C'
    )
    return dim_dic_err(regulator(ret), FPGA_REG_ERR_CODE)
