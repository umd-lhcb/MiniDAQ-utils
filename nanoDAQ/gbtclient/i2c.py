#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Wed Dec 04, 2019 at 02:01 AM -0500

import pydim
import logging

from .common import GBT_PREF, GBT_SERV
from .common import fill


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
           data='\0', filepath=None,
           gbt_serv=GBT_SERV):
    cmd = ','.join((mode, gbt, sca, bus, addr, sub_addr, size,
                   i2c_type, i2c_freq, scl))
    if filepath:
        cmd += ',{}'.format(filepath)
    cmd = fill(cmd)

    logging.debug('First argument: {}'.format(cmd))
    logging.debug('Second argument: {}'.format(data))

    args = (cmd, data)
    res = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndI2COperation'.format(GBT_PREF, gbt_serv),
        args, 'C:128;C')

    return res


def i2c_write(*args, gbt_serv=GBT_SERV, **kwargs):
    status = i2c_op(I2C_OP_MODES['write'], *args, gbt_serv=gbt_serv, **kwargs)

    if status:
        return pydim.dic_sync_info_service('{}/{}/SrvcI2CWrite'.format(
            GBT_PREF, gbt_serv))
    else:
        raise ValueError('The command was not successfully sent.')


def i2c_read(*args, gbt_serv=GBT_SERV, **kwargs):
    status = i2c_op(I2C_OP_MODES['read'], *args, gbt_serv=gbt_serv, **kwargs)

    if status:
        return pydim.dic_sync_info_service('{}/{}/SrvcI2CRead'.format(
            GBT_PREF, gbt_serv))
    else:
        raise ValueError('The command was not successfully sent.')
