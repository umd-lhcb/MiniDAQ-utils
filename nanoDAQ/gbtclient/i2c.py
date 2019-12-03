#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Dec 02, 2019 at 11:32 PM -0500

import pydim

from .common import GBT_PREF, GBT_SERV

I2C_OP_MODES = {
    'write':         '0',
    'read':          '1',
    'writeread':     '2',
    'activate_ch':   '3',
    'deactivate_ch': '4'
}

I2C_TYPE = {
    'gbtx': '0',
    'salt': '1'
}

I2C_FREQ = {
    '1MHz':   '3',
    '400KHz': '2',
    '200KHz': '1',
    '100KHz': '0'
}


def i2c_op(mode, gbt, sca, bus, addr, sub_addr, size,
           i2c_type, i2c_freq,
           scl='0',
           data='', filepath=None,
           gbt_pref=GBT_PREF, gbt_serv=GBT_SERV):
    cmd = ','.join((mode, gbt, sca, bus, addr, sub_addr, size,
                   i2c_type, i2c_freq, scl))
    if filepath:
        cmd += ',{}'.format(filepath)

    args = (cmd, data)
    res = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndI2COperation'.format(gbt_pref, gbt_serv),
        args, 'C:128;C')

    return res


def i2c_write(*args, **kwargs):
    return i2c_op(I2C_OP_MODES['write'], *args, **kwargs)


def i2c_read(*args, **kwargs):
    return i2c_op(I2C_OP_MODES['read'], *args, **kwargs)
