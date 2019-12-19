#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 19, 2019 at 04:47 AM -0500

from sty import fg

from nanoDAQ.elink import elink_extract_chs, check_bit_shift
from nanoDAQ.utils import most_common, exec_guard, hex_pad
from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r
from nanoDAQ.gbtclient.i2c import i2c_write
from nanoDAQ.gbtclient.i2c import I2C_TYPE, I2C_FREQ


##############################
# DCB elink phase adjustment #
##############################

DCB_ELK_PHASE_REG = {
    0: [69, 73, 77],
    1: [67, 71, 75],
    2: [93, 97, 101],
    3: [91, 95, 99],
    4: [117, 121, 125],
    5: [115, 119, 123],
    6: [141, 145, 149],
    7: [139, 143, 147],
    12: [165, 169, 173],  # NOTE: the ordering!
    13: [163, 167, 171],
    8: [189, 193, 197],
    9: [187, 191, 195],
    10: [213, 217, 221],
    11: [211, 215, 219]}

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
