#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Sun Dec 08, 2019 at 08:46 PM -0500

import pydim

from sty import fg, ef, rs

from .common import GBT_PREF, GBT_SERV, SCA_OP_MODE
from .common import hex_to_bytes
from .common import errs_factory, dim_cmd_err, dim_dic_err
from .common import default_dim_regulator as ddr


#############
# Constants #
#############

GPIO_ERR_CODE = errs_factory()

GPIO_DIR = {
    'out': '00000001',
    'in':  '00000000',
}

GPIO_DIR_LOOKUP = {int(v): k for k, v in GPIO_DIR.items()}

GPIO_LEVEL = {
    'high': '00000001',
    'low':  '00000000',
}

GPIO_LEVEL_INVERSE = {int(v): k for k, v in GPIO_LEVEL.items()}

GPIO_LEVEL_LOOKUP = {
    1: fg.green+ef.bold+'H'+rs.bold_dim+fg.rs,
    0: fg.red+ef.bold+'L'+rs.bold_dim+fg.rs,
}


###################
# GPIO Operations #
###################

def gpio_op(mode, gbt, sca, addr, data=None):
    cmd = ','.join(map(str,
                       (mode, gbt, sca, addr)))

    if not data:
        data = '0'
    data = hex_to_bytes(data)

    args = (cmd, data)
    ret = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndGPIOOperation'.format(GBT_PREF, GBT_SERV),
        args, 'C:128;C')
    dim_cmd_err(ret)


def gpio_write(*args, regulator=ddr, **kwargs):
    gpio_op(SCA_OP_MODE['write'], *args, **kwargs)
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcGPIOWrite'.format(GBT_PREF, GBT_SERV),
        'I:1'
    )
    return dim_dic_err(regulator(ret), GPIO_ERR_CODE)


def gpio_read(*args, regulator=ddr, **kwargs):
    gpio_op(SCA_OP_MODE['read'], *args, **kwargs)
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcGPIORead'.format(GBT_PREF, GBT_SERV),
        'I:1;C'
    )
    return dim_dic_err(regulator(ret), GPIO_ERR_CODE)


def gpio_activate_ch(gbt, sca, **kwargs):
    gpio_op(SCA_OP_MODE['activate_ch'], gbt, sca, 0, **kwargs)


######################
# GPIO line settings #
######################

def gpio_setdir(*args, direction='out', **kwargs):
    gpio_op(SCA_OP_MODE['gpio_setdir'], *args,
            data=GPIO_DIR[direction], **kwargs)


def gpio_setline(*args, level='high', **kwargs):
    gpio_op(SCA_OP_MODE['gpio_setline'], *args,
            data=GPIO_LEVEL[level], **kwargs)


def gpio_getdir(*args, regulator=ddr, **kwargs):
    gpio_op(SCA_OP_MODE['gpio_getdir'], *args, **kwargs)
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcGPIORead'.format(GBT_PREF, GBT_SERV),
        'I:1;C'
    )
    return int(dim_dic_err(regulator(ret), GPIO_ERR_CODE), base=16)


def gpio_getline(*args, regulator=ddr, **kwargs):
    gpio_op(SCA_OP_MODE['gpio_getline'], *args, **kwargs)
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcGPIORead'.format(GBT_PREF, GBT_SERV),
        'I:1;C'
    )
    return int(dim_dic_err(regulator(ret), GPIO_ERR_CODE), base=16)
