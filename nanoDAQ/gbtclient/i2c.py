#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 05, 2019 at 01:11 AM -0500

import pydim

from .common import GBT_PREF, GBT_SERV, SCA_OP_MODE
from .common import fill, hex_to_bytes
from .common import errs_factory, dim_cmd_err, dim_dic_err
from .common import default_dim_regulator as ddr


#############
# Constants #
#############

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

I2C_ERR_CODE = errs_factory({
    0x3:   'Master GBT not locked.',
    0x200: 'I2C channel not activated.',
})


##################
# I2C Operations #
##################

def i2c_op(mode, gbt, sca, bus, addr, sub_addr, size, i2c_type, i2c_freq,
           scl=0, filepath=None, data=None,
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

    args = (cmd, data)
    ret_code = pydim.dic_sync_cmnd_service(
        '{}/{}/CmndI2COperation'.format(GBT_PREF, gbt_serv),
        args, 'C:128;C')
    dim_cmd_err(ret_code)


def i2c_write(*args, gbt_serv=GBT_SERV, regulator=ddr, **kwargs):
    i2c_op(SCA_OP_MODE['write'], *args, gbt_serv=gbt_serv, **kwargs)
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcI2CWrite'.format(GBT_PREF, gbt_serv),
        'I:1'
    )
    return dim_dic_err(regulator(ret), I2C_ERR_CODE)


def i2c_read(*args, gbt_serv=GBT_SERV, regulator=ddr, **kwargs):
    i2c_op(SCA_OP_MODE['read'], *args, gbt_serv=gbt_serv, **kwargs)
    ret = pydim.dic_sync_info_service(
        '{}/{}/SrvcI2CRead'.format(GBT_PREF, gbt_serv),
        'I:1;C'
    )
    return dim_dic_err(regulator(ret), I2C_ERR_CODE)


def i2c_activate_ch(gbt, sca, bus, **kwargs):
    i2c_op(SCA_OP_MODE['activate_ch'], gbt, sca, bus, 0, 0, 0, 0, 0, **kwargs)
