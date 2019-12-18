#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Wed Dec 18, 2019 at 01:36 PM -0500

from sty import fg

from nanoDAQ.elink import elink_extract_chs, check_bit_shift
from nanoDAQ.utils import most_common, exec_guard
from nanoDAQ.ut.dcb import ELK_VALID_PHASE
from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r


##############################
# Phase alignment operations #
##############################

def loop_through_elink_phase(dcb, slave, daq_chs):
    result = dict()

    for ph in ELK_VALID_PHASE:
        for ch in daq_chs:
            exec_guard(dcb.elk_phase(ch, ph, slaves=[slave]))

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
            shift = check_bit_shift(mode)

            if freq == num_of_frame and shift >= 0:
                printout[idx].append(mode)
            elif shift >= 0:
                printout[idx].append(fg.li_yellow+mode+fg.rs)
            else:
                printout[idx].append(fg.li_red+'X'+fg.rs)

    return printout
