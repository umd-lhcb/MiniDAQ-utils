#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Dec 06, 2019 at 03:34 AM -0500

from tabulate import tabulate

from ..gbtclient.i2c import I2C_TYPE, I2C_FREQ
from ..gbtclient.i2c import i2c_activate_ch, i2c_read, i2c_write

from ..gbtclient.gpio import gpio_activate_ch, gpio_setdir, gpio_setline

from ..utils import num_of_byte

SALT_SER_SRC_MODE = {
    'fixed': '22',
    'prbs':  '03',
    'tfc':   '01',
}

SALT_INIT_SEQ = {
    (0, 4, '8c'),
    (0, 6, '15'),
    (0, 4, 'cc'),
    (0, 0, SALT_SER_SRC_MODE['fixed']),
    (0, 1, 'c4'),  # Fixed pattern to 0xC4
    (0, 8, '01'),
    (3, 0, '24'),
    (3, 1, '32'),
    (3, 0, 'e4'),
    (0, 2, '0f'),
    (0, 3, '4c'),
    (5, 6, '01'),
    (5, 7, '01'),
    (0, 8, '00'),  # Phase
}


class SALT(object):
    def __init__(self, gbt, bus, sca=0, asics=list(range(4)),
                 i2c_type=I2C_TYPE['salt'], i2c_freq=I2C_FREQ['100KHz']):
        self.gbt = gbt
        self.bus = bus
        self.sca = sca
        self.asics = asics
        self.i2c_type = i2c_type
        self.i2c_freq = i2c_freq

        self.gpio_activated = False
        self.i2c_activated = False

    def init(self, asics=None):
        asics = self.asics if asics is None else asics
        self.activate_i2c()
        self.activate_gpio()
        self.reset()
        for s in asics:
            for addr, subaddr, val in SALT_INIT_SEQ:
                i2c_write(self.gbt, self.sca, self.bus, addr+s*10, subaddr, 1,
                          self.i2c_type, self.i2c_freq, data=val)

    def write(self, addr, subaddr, data, asics=None):
        asics = self.asics if asics is None else asics
        self.activate_i2c()
        for s in asics:
            i2c_write(self.gbt, self.sca, self.bus, addr+s*10, subaddr,
                      num_of_byte(data),
                      self.i2c_type, self.i2c_freq, data=data)

    def read(self, addr, subaddr, size, asics=None, output=True):
        asics = self.asics if asics is None else asics
        self.activate_i2c()
        table = []
        for s in asics:
            addr += s*10
            value = i2c_read(self.gbt, self.sca, self.bus, addr, subaddr,
                             size, self.i2c_type, self.i2c_freq)
            table.append([str(s), hex(addr), value])

        if output:
            print(tabulate(table, headers=['SALT', 'address', 'value']))
        else:
            return table

    def reset(self, final_state='hight'):
        self.activate_gpio()
        gpio_setdir(self.gbt, self.sca, self.bus)
        gpio_setline(self.gbt, self.sca, self.bus, level='low')
        gpio_setline(self.gbt, self.sca, self.bus, level=final_state)

    def phase(self, ph, asics=None):
        asics = self.asics if asics is None else asics
        for s in asics:
            i2c_write(self.gbt, self.sca, self.bus, 0+s*10, 0x08, 1,
                      self.i2c_type, self.i2c_freq, data=ph)

    def ser_src(self, src, asics=None):
        asics = self.asics if asics is None else asics
        try:
            mode = SALT_SER_SRC_MODE[src]
        except KeyError:
            mode = src
        for s in asics:
            i2c_write(self.gbt, self.sca, self.bus, 0+s*10, 0x00, 1,
                      self.i2c_type, self.i2c_freq, mode)

    def activate_i2c(self):
        if not self.i2c_activated:
            i2c_activate_ch(self.gbt, self.sca, self.bus)
            self.i2c_activated = True

    def activate_gpio(self):
        if not self.gpio_activated:
            gpio_activate_ch(self.gbt, self.sca)
            self.gpio_activated = True
