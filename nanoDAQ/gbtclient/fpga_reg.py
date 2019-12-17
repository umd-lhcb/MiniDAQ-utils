#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Dec 17, 2019 at 04:36 AM -0500

import pydim

from .common import GBT_PREF, GBT_SERV, TELL40
from .common import errs_factory, dim_cmd_err, dim_dic_err
from .common import default_dim_regulator as ddr

from ..utils import chunks, exec_guard
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
        return [int(m) for m in mem]
    elif isinstance(mem, str):
        return [ord(m) for m in mem]


def mem_mon_regulator(tp):
    mem = mem_mon_decode(tp[1])
    elk_df_lst = list(map(elink_parser, chunks(mem)))
    return (tp[0], elk_df_lst)


def fiber_channel(n):
    ch_str = hex(1 << n)[2:]
    ch_padded = ch_str.rjust(8, '0')
    return bytes.fromhex(ch_padded)


def mem_mon_read(tell40=TELL40, regulator=mem_mon_regulator):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40_monitoring.memory'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['read'], '0'), 'C:1;C')
    dim_cmd_err(ret)

    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcReadings/{}.top_tell40_monitoring.memory'.format(
            GBT_PREF, GBT_SERV, tell40), 'I:1;C')
    return dim_dic_err(regulator(ret), FPGA_REG_ERR_CODE)


def mem_mon_fiber_write(fiber, tell40=TELL40):
    fiber = fiber_channel(fiber)
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40.monitoring_fiber'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['write'], fiber), 'C:1;C')
    dim_cmd_err(ret)


def mem_mon_fiber_read(tell40=TELL40, regulator=ddr):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40.monitoring_fiber'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['read'], '0'), 'C:1;C')
    dim_cmd_err(ret)

    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcReadings/{}.top_tell40.monitoring_fiber'.format(
            GBT_PREF, GBT_SERV, tell40), 'I:1;C')
    return dim_dic_err(regulator(ret), FPGA_REG_ERR_CODE)


def mem_mon_options_write(opts=b'\x00\x00\x00\x1c', tell40=TELL40):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40.monitoring_options'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['write'], opts), 'C:1;C')
    dim_cmd_err(ret)


def mem_mon_options_read(tell40=TELL40, regulator=ddr):
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndOperation/{}.top_tell40.monitoring_options'.format(
            GBT_PREF, GBT_SERV, tell40),
        (FPGA_REG_OP_MODE['read'], '0'), 'C:1;C')
    dim_cmd_err(ret)

    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcReadings/{}.top_tell40.monitoring_options'.format(
            GBT_PREF, GBT_SERV, tell40), 'I:1;C')
    return dim_dic_err(regulator(ret), FPGA_REG_ERR_CODE)


# Wrap FPGA operations so that they run in separate processes.
mem_mon_read_safe = lambda *args, **kwargs: \
    exec_guard(mem_mon_read, args, kwargs)
mem_mon_fiber_write_safe = lambda *args, **kwargs: \
    exec_guard(mem_mon_fiber_write, *args, **kwargs)
mem_mon_fiber_read_safe = lambda *args, **kwargs: \
    exec_guard(mem_mon_fiber_read, *args, **kwargs)
mem_mon_options_write_safe = lambda *args, **kwargs: \
    exec_guard(mem_mon_options_write, *args, **kwargs)
mem_mon_options_read_safe = lambda *args, **kwargs: \
    exec_guard(mem_mon_options_read, *args, **kwargs)
