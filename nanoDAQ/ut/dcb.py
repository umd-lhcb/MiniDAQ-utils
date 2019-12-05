#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 05, 2019 at 06:03 AM -0500

import os.path as p

from sty import fg, ef, rs
from tabulate import tabulate

from ..gbtclient.i2c import I2C_TYPE, I2C_FREQ
from ..gbtclient.i2c import i2c_activate_ch, i2c_read, i2c_write

from ..gbtclient.gpio import GPIO_LEVEL_LOOKUP
from ..gbtclient.gpio import gpio_activate_ch, gpio_setdir, gpio_setline, \
    gpio_getline

from ..utils import dict_factory, num_of_byte


GBTX_STATUS = dict_factory({
    0x61: fg.green+ef.bold+'Idle'+rs.bold_dim+fg.rs,
    0x15: fg.yellow+ef.bold+'Pause for config'+rs.bold_dim+fg.rs,
}, 'Unknown state')


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
        slaves = self.slaves if slaves is None else slaves
        self.activate_i2c()
        filepath = p.abspath(p.expanduser(filepath))
        for s in slaves:
            i2c_write(self.gbt, self.sca, self.bus, s, 0, 366,
                      self.i2c_type, self.i2c_freq, filepath=filepath)

    def write(self, subaddr, data, slaves=None):
        slaves = self.slaves if slaves is None else slaves
        self.activate_i2c()
        for s in slaves:
            i2c_write(self.gbt, self.sca, self.bus, s, subaddr,
                      num_of_byte(data),
                      self.i2c_type, self.i2c_freq, data=data)

    def gpio_reset(self, chs):
        self.activate_gpio()
        for c in chs:
            gpio_setdir(self.gbt, self.sca, c)
            gpio_setline(self.gbt, self.sca, c, level='low')
            gpio_setline(self.gbt, self.sca, c, level='high')

    def slave_status(self):
        self.active_i2c()
        table = []
        for s in self.slaves:
            status = i2c_read(self.gbt, self.sca, self.bus, s, 0x1af, 1,
                              self.i2c_type, self.i2c_freq)
            table.append([str(s), status])
        print(tabulate(table, headers=['slave', 'status']))

    def gpio_status(self):
        self.activate_gpio()
        table = []
        for g in self.gpio_chs:
            status = int(gpio_getline(self.gbt, self.sca, g))
            status = GPIO_LEVEL_LOOKUP[status]
            table.append([str(g), status])
        print(tabulate(table, headers=['GPIO', 'status']))

    def activate_i2c(self):
        if not self.i2c_activated:
            i2c_activate_ch(self.gbt, self.sca, self.bus)
            self.i2c_activated = True

    def activate_gpio(self):
        if not self.gpio_activated:
            gpio_activate_ch(self.gbt, self.sca)
            self.i2c_activated = True
