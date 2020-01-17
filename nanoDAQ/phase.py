#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Jan 17, 2020 at 03:10 AM -0500

from collections import defaultdict, Counter
from sty import fg

from nanoDAQ.elink import elink_extract_chs, check_bit_shift
from nanoDAQ.utils import most_common, exec_guard, hex_pad

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r

from nanoDAQ.ut.salt import salt_cur_elk_phase, salt_elk_phase, \
    salt_ser_src, salt_tfc_phase, \
    SALT_TFC_VALID_PHASE
from nanoDAQ.ut.dcb import dcb_elk_phase, DCB_ELK_VALID_PHASE


###################################
# DCB/SALT I2C operation wrappers #
###################################

def adj_dcb_elink_phase(adjustment, gbt, slave):
    for ch, ph in adjustment.items():
        exec_guard(dcb_elk_phase, gbt, slave, ch, ph)


def adj_salt_elink_phase(pattern, gbt, bus, asic):
    phase = check_bit_shift(pattern)

    if phase:
        cur_phase = int(exec_guard(salt_cur_elk_phase, gbt, bus, asic))
        phase = (phase + cur_phase) % 8
        print('SALT current phase is {}, shifting to {}'.format(
            cur_phase, phase))
        exec_guard(salt_elk_phase, gbt, bus, asic, str(phase))


def salt_tfc_mode(gbt, bus, asic, mode='tfc'):
    exec_guard(salt_ser_src, gbt, bus, asic, mode)


def adj_salt_tfc_phase(daq_chs, gbt, bus, asic):
    for ph in SALT_TFC_VALID_PHASE:
        exec_guard(salt_tfc_phase, gbt, bus, asic, ph)
        mem = elink_extract_chs(mem_r(), daq_chs)

        good_chs = []
        for ch, data in mem.items():
            mode, _ = most_common(data)
            if 0x04 == mode:
                good_chs.append(ch)

        if sorted(good_chs) == sorted(daq_chs):
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


####################################
# Elink phase alignment operations #
####################################

def loop_phase_elk(daq_chs, gbt, slave,
                   phases=DCB_ELK_VALID_PHASE, phase_tuner=dcb_elk_phase):
    loop_result = dict()

    for ph in phases:
        for ch in daq_chs:
            exec_guard(phase_tuner, gbt, slave, ch, ph)

        loop_result[ph] = elink_extract_chs(mem_r(), daq_chs)

    return loop_result


def check_elem_continuous(elem, lst):
    if not lst:
        return True
    elif 1 == abs(int(elem, base=16) - int(lst[-1], base=16)):
        return True
    else:
        return False


def scan_phase_elink_selector(mode, freq, num_of_frame, shift, idx, ph, ch,
                              printout, good_patterns_chs):
    if freq == num_of_frame and shift >= 0:
        printout[idx].append(mode)
        if check_elem_continuous(
                ph, good_patterns_chs[ch][mode]):
            good_patterns_chs[ch][mode].append(ph)
    elif shift >= 0:
        printout[idx].append(fg.li_yellow+mode+fg.rs)
    else:
        printout[idx].append(fg.li_red+'X'+fg.rs)


def scan_phase_elink(loop_result, phases=DCB_ELK_VALID_PHASE,
                     selector=scan_phase_elink_selector):
    printout = [list() for _ in range(len(phases)+1)]
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

    # Now try to find optimum phases.
    common_patterns = intersect_good_pattern(good_patterns_chs)

    # Local optimal: Picking the longest good phase for the first channel.
    # NOTE: This algorithm should be stable.
    first_ch = next(iter(good_patterns_chs))
    common_patterns_freq = {k: len(good_patterns_chs[first_ch][k])
                            for k in common_patterns}
    pattern = Counter(common_patterns_freq).most_common(1)[0][0]
    phase_per_ch = {ch: mid_elem(good_patterns_chs[ch][pattern])
                    for ch in good_patterns_chs.keys()}

    good_phase_printout = [phase_per_ch[i]
                           for i in sorted(phase_per_ch, reverse=True)]

    # Update printout table.
    for idx, ph in enumerate(good_phase_printout):
        ph = int(ph, base=16)
        printout[ph][idx+1] = fg.li_green + printout[ph][idx+1] + fg.rs

    return printout, phase_per_ch, int(pattern, base=16)
