#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Dec 09, 2019 at 01:59 AM -0500

import pydim

from .common import GBT_PREF, GBT_SERV, TELL40
from .common import errs_factory, dim_cmd_err, dim_dic_err
from .common import default_dim_regulator as ddr

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
    elk_df_lst = list(map(elink_parser, chunks(mem)))
    return (tp[0], elk_df_lst)


def mem_mon_read(tell40=TELL40, regulator=mem_mon_regulator):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40_monitoring.memory'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['read'], '1'), 'C:1;C')
    dim_cmd_err(ret)

    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcReadings/{}.top_tell40_monitoring.memory'.format(
            GBT_PREF, GBT_SERV, tell40), 'I:1;C')
    return dim_dic_err(regulator(ret), FPGA_REG_ERR_CODE)


def mem_mon_fiber_write(fiber, tell40=TELL40):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40.monitoring_fiber'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['write'], fiber), 'C:1;C')
    dim_cmd_err(ret)


def mem_mon_fiber_read(fiber, tell40=TELL40, regulator=ddr):
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcReadings/{}.top_tell40.monitoring_fiber'.format(
            GBT_PREF, GBT_SERV, tell40), 'C:1;C')
    return dim_dic_err(regulator(ret), FPGA_REG_ERR_CODE)


def mem_mon_options_write(opts, tell40=TELL40):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40.monitoring_options'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['write'], opts), 'C:1;C')
    dim_cmd_err(ret)


def mem_mon_options_read(fiber, tell40=TELL40, regulator=ddr):
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcReadings/{}.top_tell40.monitoring_options'.format(
            GBT_PREF, GBT_SERV, tell40), 'C:1;C')
    return dim_dic_err(regulator(ret), FPGA_REG_ERR_CODE)
