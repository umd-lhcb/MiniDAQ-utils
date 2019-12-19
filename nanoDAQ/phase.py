#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 19, 2019 at 02:46 AM -0500

from sty import fg

from nanoDAQ.elink import elink_extract_chs, check_bit_shift
from nanoDAQ.utils import most_common, exec_guard, hex_pad
from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r
from nanoDAQ.gbtclient.i2c import i2c_write
from nanoDAQ.gbtclient.i2c import I2C_TYPE, I2C_FREQ


##############################
# DCB elink phase adjustment #
##############################

DCB_ELK_PHASE_REG = {}
for ch in range(0, 14, 2):
    reg_a = 69 + 12*ch  # Magic numbers: 69 and 12. See GBTX manual.
    reg_tri = [reg_a+i for i in [0, 4, 8]]
    DCB_ELK_PHASE_REG[ch] = reg_tri
    DCB_ELK_PHASE_REG[ch+1] = list(map(lambda x: x-2, reg_tri))

DCB_ELK_VALID_PHASE = list(map(lambda x: hex(x)[2:], range(15)))


def dcb_elk_phase(gbt, slave, ch, phase):
    for reg in DCB_ELK_PHASE_REG[ch]:
        i2c_write(gbt, 0, 6, slave, reg, 1, I2C_TYPE['gbtx'], I2C_FREQ['1MHz'],
                  data=phase*2)


##############################
# Phase alignment operations #
##############################

def loop_through_elink_phase(gbt, slave, daq_chs):
    result = dict()

    for ph in DCB_ELK_VALID_PHASE:
        for ch in daq_chs:
            exec_guard(dcb_elk_phase, gbt, slave, ch, ph)

        result[ph] = elink_extract_chs(mem_r(), daq_chs)

    return result


def check_phase_scan(scan):
    printout = [list() for i in range(15)]

    for ph, chs_data in scan.items():
        idx = int(ph, base=16)
        printout[idx].append(ph)
        for ch, data in chs_data.items():
            num_of_frame = len(data)
            mode, freq = most_common(data)
            mode_display = hex_pad(mode)
            shift = check_bit_shift(mode)

            if freq == num_of_frame and shift >= 0:
                printout[idx].append(mode_display)
            elif shift >= 0:
                printout[idx].append(fg.li_yellow+mode_display+fg.rs)
            else:
                printout[idx].append(fg.li_red+'X'+fg.rs)

    return printout
