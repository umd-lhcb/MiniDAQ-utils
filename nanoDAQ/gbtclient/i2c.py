#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Wed Dec 04, 2019 at 03:40 AM -0500

import pydim
import logging

from .common import GBT_PREF, GBT_SERV
from .common import fill, hex_to_bytes
from .common import default_dim_regulator as ddr


#############
# Constants #
#############

I2C_OP_MODES = {
    'write':         0,
    'read':          1,
    'writeread':     2,
    'activate_ch':   3,
    'deactivate_ch': 4,
}

I2C_TYPE = {
    'gbtx': 0,
    'salt': 1,
}

I2C_FREQ = {
    '100KHz': 0,
    '200KHz': 1,
    '400KHz': 2,
    '1MHz':   3,
}

I2C_ERROR_CODE = {
    3:   'Master GBT not locked.',
    512: 'I2C channel not activated.',
}


##################
# I2C Operations #
##################

def i2c_op(mode, gbt, sca, bus, addr, sub_addr, size,
           i2c_type, i2c_freq,
           scl=0,
           data=None, filepath=None,
           gbt_serv=GBT_SERV):
    cmd = ','.join(map(str,
                       (mode, gbt, sca, bus, addr, sub_addr, size,
                        i2c_type, i2c_freq, scl)))
    if filepath:
        cmd += ',{}'.format(filepath)
    cmd = fill(cmd)

    if not data:
        data = '0'
    data = hex_to_bytes(data)

    logging.debug('First argument: {}'.format(cmd))
    logging.debug('Second argument: {}'.format(data))

    args = (cmd, data)
    res = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndI2COperation'.format(GBT_PREF, gbt_serv),
        args, 'C:128;C')

    return res


def i2c_write(*args, gbt_serv=GBT_SERV, regulator=ddr, **kwargs):
    status = i2c_op(I2C_OP_MODES['write'], *args, gbt_serv=gbt_serv, **kwargs)

    if status:
        return regulator(pydim.dic_sync_info_service('{}/{}/SrvcI2CWrite'.format(
            GBT_PREF, gbt_serv)))
    else:
        raise ValueError('The command was not successfully sent.')


def i2c_read(*args, gbt_serv=GBT_SERV, regulator=ddr, **kwargs):
    status = i2c_op(I2C_OP_MODES['read'], *args, gbt_serv=gbt_serv, **kwargs)

    if status:
        return regulator(pydim.dic_sync_info_service('{}/{}/SrvcI2CRead'.format(
            GBT_PREF, gbt_serv)))
    else:
        raise ValueError('The command was not successfully sent.')
