#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Wed Dec 11, 2019 at 06:18 PM -0500

import os.path as op

from time import sleep
from sty import fg, ef, rs
from tabulate import tabulate

from ..gbtclient.i2c import I2C_TYPE, I2C_FREQ
from ..gbtclient.i2c import i2c_activate_ch, i2c_read, i2c_write

from ..gbtclient.gpio import GPIO_DIR_LOOKUP, GPIO_LEVEL_LOOKUP
from ..gbtclient.gpio import gpio_activate_ch, gpio_setdir, gpio_setline, \
    gpio_getdir, gpio_getline

from ..utils import dict_factory, num_of_byte, hex_pad


GBTX_STATUS = dict_factory({
    '61': fg.green+ef.bold+'Idle'+rs.bold_dim+fg.rs,
    '15': fg.yellow+ef.bold+'Pause for config'+rs.bold_dim+fg.rs,
}, 'Unknown state')

PRBS_MODE = {
    'on':  '03',
    'off': '00',
}


class DCB(object):
    def __init__(self, gbt, sca=0, bus=6, slaves=list(range(1, 7)),
                 i2c_type=I2C_TYPE['gbtx'], i2c_freq=I2C_FREQ['1MHz']):
        self.gbt = gbt
        self.sca = sca
        self.bus = bus
        self.slaves = slaves
        self.i2c_type = i2c_type
        self.i2c_freq = i2c_freq

        self.gpio_activated = False
        self.gpio_chs = list(range(0, 7))

        self.i2c_activated = False

    def init(self, filepath, slaves=None):
        self.activate_i2c()
        filepath = op.abspath(op.expanduser(filepath))

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0, 366,
                      self.i2c_type, self.i2c_freq, filepath=filepath)

    def write(self, subaddr, data, slaves=None):
        self.activate_i2c()

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, subaddr,
                      num_of_byte(data),
                      self.i2c_type, self.i2c_freq, data=data)

    def read(self, subaddr, size, slaves=None, output=True):
        self.activate_i2c()
        table = []

        for s in self.dyn_slaves(slaves):
            value = i2c_read(self.gbt, self.sca, self.bus, s, subaddr, size,
                             self.i2c_type, self.i2c_freq)
            table.append([s, value])

        if output:
            print(tabulate(table, headers=['slave', 'value']))
        else:
            return table

    def slave_status(self, slaves=None, output=True):
        self.activate_i2c()
        table_raw = []
        table = []

        for s in self.dyn_slaves(slaves):
            status = i2c_read(self.gbt, self.sca, self.bus, s, 0x1af, 1,
                              self.i2c_type, self.i2c_freq)
            table_raw.append([s, status])
            table.append([s, GBTX_STATUS[status]])

        if output:
            print(tabulate(table, headers=['slave', 'value']))
        else:
            return table_raw

    def gpio_status(self, output=True):
        self.activate_gpio()
        table_raw = []
        table = []

        for g in self.gpio_chs:
            dir = gpio_getdir(self.gbt, self.sca, g)
            line = gpio_getline(self.gbt, self.sca, g)

            table_raw.append([g, dir, line])
            table.append([g, GPIO_DIR_LOOKUP[dir], GPIO_LEVEL_LOOKUP[line]])

        if output:
            print(tabulate(table, headers=['GPIO', 'direction', 'status'],
                           colalign=['right', 'left', 'left']))
        else:
            return table_raw

    def gpio_reset(self, chs, final_state='high'):
        self.activate_gpio()

        for c in chs:
            gpio_setdir(self.gbt, self.sca, c)
            gpio_setline(self.gbt, self.sca, c, level='low')
            gpio_setline(self.gbt, self.sca, c, level=final_state)

    def prbs(self, mode, slaves=None):
        try:
            val = PRBS_MODE[mode]
        except KeyError:
            val = mode

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0x1c, 1,
                      self.i2c_type, self.i2c_freq, data=val)

    def reset(self, final_state='high'):
        self.gpio_reset(chs=[6])

    def bias_cur_status(self, slaves=None, output=True):
        self.activate_i2c()
        self.gbld_addr(slaves)
        table_raw = []
        table = []

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0x185, 1,
                      self.i2c_type, self.i2c_freq, data='c4')
            sleep(0.08)  # FIXME: Needed for unknown reason
            reg = i2c_read(self.gbt, self.sca, self.bus, s, 0x17f, 1,
                           self.i2c_type, self.i2c_freq)
            cur = self.gbld_reg_to_cur(reg)
            table_raw.append([s, cur])

            if cur <= 8.5:
                cur_fmt = fg.green+ef.bold+cur+rs.bold_dim+fg.rs
            else:
                cur_fmt = fg.yellow+ef.bold+cur+rs.bold_dim+fg.rs
            table.append([s, cur_fmt])

        if output:
            print(tabulate(table, headers=['slave', 'current [mA]']))
        else:
            return table_raw

    def bias_cur_set(self, cur, slaves=None):
        self.activate_i2c()
        reg = self.gbld_cur_to_reg(cur)
        gbld_conf = '8799{}88ffff04'.format(reg)

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0x37, 7,
                      self.i2c_type, self.i2c_freq, data=gbld_conf)

        sleep(0.1)
        self.gbld_addr(slaves)
        sleep(0.1)  # FIXME: Needed for unknown reason

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0x184, 1,
                      self.i2c_type, self.i2c_freq, data='c4')
            sleep(0.05)

    def gbld_addr(self, slaves=None):
        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0xfd, 1,
                      self.i2c_type, self.i2c_freq, data='7e')

    def activate_i2c(self):
        if not self.i2c_activated:
            i2c_activate_ch(self.gbt, self.sca, self.bus)
            self.i2c_activated = True

    def activate_gpio(self):
        if not self.gpio_activated:
            gpio_activate_ch(self.gbt, self.sca)
            self.gpio_activated = True

    def dyn_slaves(self, slaves):
        return self.slaves if slaves is None else slaves

    @staticmethod
    def gbld_reg_to_cur(reg):
        return 2 + 0.16*int(reg, base=16)

    @classmethod
    def gbld_cur_to_reg(cls, cur):
        for reg in range(256):
            if cls.gbld_reg_to_cur(reg) < cur:
                pass
            else:
                return hex_pad(reg)
