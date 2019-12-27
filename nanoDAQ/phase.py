#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Dec 20, 2019 at 07:21 PM -0500

from collections import defaultdict
from sty import fg

from nanoDAQ.elink import elink_extract_chs, check_bit_shift
from nanoDAQ.utils import most_common, exec_guard, hex_pad, pad

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r
from nanoDAQ.gbtclient.i2c import i2c_write
from nanoDAQ.gbtclient.i2c import I2C_TYPE, I2C_FREQ

from nanoDAQ.ut.salt import SALT, SALT_SER_SRC_MODE
from nanoDAQ.ut.dcb import dcb_elk_phase


##############################
# DCB elink phase adjustment #
##############################

def adj_dcb_elink_phase(adjustment, gbt, slave):
    for ch, ph in adjustment.items():
        exec_guard(dcb_elk_phase, gbt, slave, ch, ph)


###############################
# SALT elink phase adjustment #
###############################

def salt_elk_phase(gbt, bus, asic, phase):
    i2c_write(gbt, 0, bus, SALT.addr_shift(0, asic), 8, 1,
              I2C_TYPE['salt'], I2C_FREQ['100KHz'], data=pad(phase))


def adj_salt_elink_phase(pattern, gbt, bus, asic):
    phase = check_bit_shift(pattern)
    if phase:
        print('Shift SALT elink phase to {}'.format(phase))
        exec_guard(salt_elk_phase, gbt, bus, asic, str(phase))


#############################
# SALT TFC phase adjustment #
#############################

SALT_TFC_VALID_PHASE = ['03', '07', '0b', '0f', '13', '17', '1b', '1f']


def salt_ser_src(gbt, bus, asic, mode):
    i2c_write(gbt, 0, bus, SALT.addr_shift(0, asic), 0, 1,
              I2C_TYPE['salt'], I2C_FREQ['100KHz'],
              data=SALT_SER_SRC_MODE[mode])


def salt_tfc_mode(gbt, bus, asic, mode='tfc'):
    exec_guard(salt_ser_src, gbt, bus, asic, mode)


def salt_tfc_phase(gbt, bus, asic, phase):
    i2c_write(gbt, 0, bus, SALT.addr_shift(0, asic), 2, 1,
              I2C_TYPE['salt'], I2C_FREQ['100KHz'], data=pad(phase))


def adj_salt_tfc_phase(daq_chs, gbt, bus, asic):
    for ph in SALT_TFC_VALID_PHASE:
        exec_guard(salt_tfc_phase, gbt, bus, asic, ph)
        mem = elink_extract_chs(mem_r(), daq_chs)

        for chs_data in mem.values():
            for data in chs_data.values():
                mode, _ = most_common(data)
                if 0x04 == mode:
                    return True

    return False


###########################
# Phase alignment helpers #
###########################

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


######################################
# General phase alignment operations #
######################################

def loop_phase(daq_chs, phases, phase_tuner, *args):
    loop_result = dict()

    for ph in phases:
        for ch in daq_chs:
            exec_guard(phase_tuner, *args, ch, ph)

        loop_result[ph] = elink_extract_chs(mem_r(), daq_chs)

    return loop_result


def scan_phase(loop_result, phases, expected, selector):
    printout = [list() for _ in range(len(phases)+1)]
    num_of_chs = len(list(loop_result.values()))
    good_patterns_chs = defaultdict(lambda: defaultdict(list))

    for ph, chs_data in loop_result.items():
        idx = int(ph, base=16)
        printout[idx].append(ph)

        for ch, data in chs_data.items():
            num_of_frame = len(data)
            mode, freq = most_common(data)
            mode_display = hex_pad(mode)
            shift = check_bit_shift(mode)

            selector(mode_display, freq, num_of_frame, shift, idx, ph, ch,
                     printout, good_patterns_chs)

    # Now try to find optimum phases
    common_patterns = intersect_good_pattern(good_patterns_chs)
    phase_per_ch = dict()

    for cp in common_patterns:
        phase_per_ch = dict()
        pattern = int(cp, base=16)
        for ch, p in good_patterns_chs.items():
            if len(p[cp]) >= 3:
                phase_per_ch[ch] = mid_elem(p[cp])

        good_phase_printout = [phase_per_ch[i]
                               for i in sorted(phase_per_ch, reverse=True)]
        if len(good_phase_printout) == num_of_chs:
            break

    # Update printout table
    for idx, ph in enumerate(good_phase_printout):
        ph = int(ph, base=16)
        printout[ph][idx+1] = fg.li_green + printout[ph][idx+1] + fg.rs

    return printout, phase_per_ch, pattern


####################################
# Elink phase alignment operations #
####################################

def loop_through_elink_phase(gbt, slave, daq_chs):
    result = dict()

    for ph in DCB_ELK_VALID_PHASE:
        for ch in daq_chs:
            exec_guard(dcb_elk_phase, gbt, slave, ch, ph)

        result[ph] = elink_extract_chs(mem_r(), daq_chs)

    return result


def check_elem_continuous(elem, lst):
    if not lst:
        return True
    elif 1 == abs(int(elem, base=16) - int(lst[-1], base=16)):
        return True
    else:
        return False


def elink_phase_scan(scan):
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
        pattern = int(cp, base=16)
        for ch, p in good_patterns_chs.items():
            if len(p[cp]) >= 3:
                phase_per_ch[ch] = mid_elem(p[cp])

        good_phase_printout = [phase_per_ch[i]
                               for i in sorted(phase_per_ch, reverse=True)]
        if len(good_phase_printout) == num_of_chs:
            break

    # Update printout table
    for idx, ph in enumerate(good_phase_printout):
        ph = int(ph, base=16)
        printout[ph][idx+1] = fg.li_green + printout[ph][idx+1] + fg.rs

    return printout, phase_per_ch, pattern


def loop_phase_elk(daq_chs, gbt, slave, phases=DCB_ELK_VALID_PHASE):
    return loop_phase(daq_chs, phases, dcb_elk_phase, gbt, slave)


##################################
# TFC phase alignment operations #
##################################

def loop_phase_tfc(*args):
    return loop_phase_elk(*args, phases=SALT_TFC_VALID_PHASE)


def scan_phase_tfc_selector(mode, freq, num_of_frame, shift, idx, ph, ch,
                            printout, good_patterns_chs):
    if (num_of_frame - freq) <= 6:
        printout[idx].append(mode)
        good_patterns_chs[ch][mode].append(ph)
    elif shift >= 0:
        printout[idx].append(fg.li_yellow + mode + fg.rs)
    else:
        printout[idx].append(fg.li_red + 'X' + fg.rs)


def scan_phase_tfc(loop_result):
    return scan_phase(loop_result, SALT_TFC_VALID_PHASE, 0x04,
                      scan_phase_tfc_selector)
