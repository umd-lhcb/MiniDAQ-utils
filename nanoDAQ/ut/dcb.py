#!/usr/bin/env python3
#
# Author: Yipeng Sun, Manuel Franco Sevilla
# License: BSD 2-clause
# Last Change: Sun Dec 29, 2019 at 10:28 PM -0500

import os.path as op

from time import sleep
from sty import fg, ef, rs
from tabulate import tabulate

from nanoDAQ.gbtclient.i2c import I2C_TYPE, I2C_FREQ
from nanoDAQ.gbtclient.i2c import i2c_activate_ch, i2c_read, i2c_write

from nanoDAQ.gbtclient.gpio import GPIO_DIR_LOOKUP, GPIO_LEVEL_LOOKUP
from nanoDAQ.gbtclient.gpio import gpio_activate_ch, gpio_setdir, \
    gpio_setline, gpio_getdir, gpio_getline

from nanoDAQ.utils import dict_factory, num_of_byte, hex_pad


#############
# Constants #
#############

GBTX_STATUS = dict_factory({
    '61': fg.green+ef.bold+'Idle'+rs.bold_dim+fg.rs,
    '15': fg.yellow+ef.bold+'Pause for config'+rs.bold_dim+fg.rs,
}, 'Unknown state')

PRBS_MODE = {
    'on':  '03',
    'off': '00',
}

DCB_SCA = 0
DCB_SLAVE_I2C_BUS = 6


###############
# Elink phase #
###############

# From Tables 36-42 in the GBTx manual 0.15.
# Registers are triple voted, so all three need to be changed
DCB_ELK_PHASE_REG = {
    0:  [189, 193, 197],  # Group 5 channel 4/5 ABC
    1:  [187, 191, 195],  # Group 5 channel 0/1 ABC
    2:  [213, 217, 221],  # Group 6 channel 4/5  ABC
    3:  [211, 215, 219],  # Group 6 channel 0/1 ABC
    4:  [69, 73, 77],     # Group 0 channel 4/5 ABC
    5:  [67, 71, 75],     # Group 0 channel 0/1 ABC
    6:  [93, 97, 101],    # Group 1 channel 4/5 ABC
    7:  [91, 95, 99],     # Group 1 channel 0/1 ABC
    8:  [117, 121, 125],  # Group 2 channel 4/5 ABC
    9:  [115, 119, 123],  # Group 2 channel 0/1 ABC
    10: [141, 145, 149],  # Group 3 channel 4/5 ABC
    11: [139, 143, 147],  # Group 3 channel 0/1 ABC
    12: [165, 169, 173],  # Group 4 channel 4/5 ABC
    13: [163, 167, 171],  # Group 4 channel 0/1 ABC
}

DCB_ELK_VALID_PHASE = list(map(lambda x: hex(x)[2:], range(15)))


# We separate this I2C operation to a separate function so that it can be easily
# wrapped in another process.
def dcb_elk_phase(gbt, slave, ch, phase):
    for reg in DCB_ELK_PHASE_REG[ch]:
        i2c_write(gbt, DCB_SCA, DCB_SLAVE_I2C_BUS,
                  slave, reg, 1, I2C_TYPE['gbtx'], I2C_FREQ['1MHz'],
                  data=phase*2)


##################
# DCB all-in-one #
##################

class DCB(object):
    def __init__(self, gbt,
                 sca=DCB_SCA, bus=DCB_SLAVE_I2C_BUS, slaves=list(range(1, 7)),
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

    ####################
    # Basic operations #
    ####################

    def init(self, filepath, slaves=None):
        self.activate_i2c()
        filepath = op.abspath(op.expanduser(filepath))

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0, 366,
                      self.i2c_type, self.i2c_freq, filepath=filepath)

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

    ##################
    # I2C write/read #
    ##################

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

    ###################################
    # Check the status of slave GBTxs #
    ###################################

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

    ###################
    # GPIO operations #
    ###################

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
            sleep(1)
            gpio_setline(self.gbt, self.sca, c, level=final_state)

    def reset(self, final_state='high'):
        self.gpio_reset(chs=[6], final_state=final_state)

    ##########################################
    # PRBS register settings for slave GBTxs #
    ##########################################

    def prbs(self, mode, slaves=None):
        try:
            val = PRBS_MODE[mode]
        except KeyError:
            val = mode

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0x1c, 1,
                      self.i2c_type, self.i2c_freq, data=val)

    #########################################
    # Bias current settings for slave GBTxs #
    #########################################

    def bias_cur_status(self, slaves=None, output=True):
        self.activate_i2c()
        self.gbld_addr(slaves)
        table_raw = []
        table = []

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0x185, 1,
                      self.i2c_type, self.i2c_freq, data='c4')
            sleep(0.08)  # Give GBTx/GBLD some time to respond
            reg = i2c_read(self.gbt, self.sca, self.bus, s, 0x17f, 1,
                           self.i2c_type, self.i2c_freq)
            cur = self.gbld_reg_to_cur(reg)
            table_raw.append([s, cur])

            if cur <= 6.1:
                cur_fmt = fg.green+ef.bold+str(cur)+rs.bold_dim+fg.rs
            else:
                cur_fmt = fg.yellow+ef.bold+str(cur)+rs.bold_dim+fg.rs
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

        self.gbld_addr(slaves)

        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0x184, 1,
                      self.i2c_type, self.i2c_freq, data='c4')
            sleep(0.08)

    def gbld_addr(self, slaves=None):
        for s in self.dyn_slaves(slaves):
            i2c_write(self.gbt, self.sca, self.bus, s, 0xfd, 1,
                      self.i2c_type, self.i2c_freq, data='7e')

    @staticmethod
    def gbld_reg_to_cur(reg):
        return 2 + 0.16*int(reg, base=16)

    @classmethod
    def gbld_cur_to_reg(cls, cur):
        for reg in range(256):
            reg = hex_pad(reg)
            if cls.gbld_reg_to_cur(reg) < cur:
                pass
            else:
                return reg

    #######################
    # Elink channel phase #
    #######################

    def elink_phase(self, ch, phase, slaves=None):
        for s in self.dyn_slaves(slaves):
            dcb_elk_phase(self.gbt, s, ch, phase)
