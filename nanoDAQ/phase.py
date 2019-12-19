#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 19, 2019 at 07:07 AM -0500

from collections import defaultdict
from sty import fg

from nanoDAQ.elink import elink_extract_chs, check_bit_shift
from nanoDAQ.utils import most_common, exec_guard, hex_pad, pad

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r
from nanoDAQ.gbtclient.i2c import i2c_write
from nanoDAQ.gbtclient.i2c import I2C_TYPE, I2C_FREQ

from nanoDAQ.ut.salt import SALT


##############################
# DCB elink phase adjustment #
##############################

DCB_ELK_PHASE_REG = {
    0: [187, 191, 195],
    1: [189, 193, 197],
    2: [211, 215, 219],
    3: [213, 217, 221],
    4: [69, 73, 77],
    5: [67, 71, 75],
    6: [93, 97, 101],
    7: [91, 95, 99],
    8: [117, 121, 125],
    9: [115, 119, 123],
    10: [141, 145, 149],
    11: [139, 143, 147],
    12: [165, 169, 173],
    13: [163, 167, 171],
}

DCB_ELK_VALID_PHASE = list(map(lambda x: hex(x)[2:], range(15)))


def dcb_elk_phase(gbt, slave, ch, phase):
    for reg in DCB_ELK_PHASE_REG[ch]:
        i2c_write(gbt, 0, 6, slave, reg, 1, I2C_TYPE['gbtx'], I2C_FREQ['1MHz'],
                  data=phase*2)


def adj_dcb_elink_phase(adjustment, gbt, slave):
    for ch, ph in adjustment.items():
        exec_guard(dcb_elk_phase, gbt, slave, ch, ph)


#########################
# SALT phase adjustment #
#########################

def salt_elk_phase(gbt, bus, asic, phase):
    i2c_write(gbt, 0, bus, SALT.addr_shift(0, asic), 8, 1,
              I2C_TYPE['salt'], I2C_FREQ['100KHz'], data=pad(phase))


def adj_salt_elink_phase(pattern, gbt, bus, asic):
    phase = check_bit_shift(pattern)
    exec_guard(salt_elk_phase, gbt, bus, asic, phase)


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


def intersect_good_pattern(ptns):
    good_patterns = []
    for _, p in ptns.items():
        good_patterns.append(list(p))

    result = set(good_patterns[0])
    for s in good_patterns[1:]:
        result.intersection_update(s)

    return result


def mid_elem(lst):
    return lst[int(len(lst)/2)]


def check_elem_continuous(elem, lst):
    if not lst:
        return True
    elif 1 == abs(int(elem, base=16) - int(lst[-1], base=16)):
        return True
    else:
        return False


def check_phase_scan(scan):
    printout = [list() for i in range(15)]
    num_of_chs = len(list(scan.values()))
    good_patterns_chs = defaultdict(lambda: defaultdict(list))

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
                if check_elem_continuous(
                        ph, good_patterns_chs[ch][mode_display]):
                    good_patterns_chs[ch][mode_display].append(ph)
            elif shift >= 0:
                printout[idx].append(fg.li_yellow+mode_display+fg.rs)
            else:
                printout[idx].append(fg.li_red+'X'+fg.rs)

    # Now try to find optimum phases
    common_patterns = intersect_good_pattern(good_patterns_chs)
    phase_per_ch = dict()

    for cp in common_patterns:
        phase_per_ch = dict()
        for ch, p in good_patterns_chs.items():
            if len(p[cp]) >= 3:
                ch = int(ch.replace('elk', ''))
                phase_per_ch[ch] = mid_elem(p[cp])

        good_phase_printout = [phase_per_ch[i]
                               for i in sorted(phase_per_ch, reverse=True)]
        if len(good_phase_printout) == num_of_chs:
            break

    # Update printout table
    for idx, ph in enumerate(good_phase_printout):
        ph = int(ph, base=16)
        printout[ph][idx+1] = fg.li_green + printout[ph][idx+1] + fg.rs

    return printout, phase_per_ch, cp  # 'cp' is the fixed pattern at good phase
