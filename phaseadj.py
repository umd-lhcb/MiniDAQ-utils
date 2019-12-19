#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 19, 2019 at 06:22 AM -0500

from argparse import ArgumentParser
from tabulate import tabulate

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r
from nanoDAQ.gbtclient.fpga_reg import mem_mon_fiber_write_safe as fiber_w
from nanoDAQ.gbtclient.fpga_reg import mem_mon_options_write_safe as opts_w

from nanoDAQ.elink import print_elink_table, alternating_color
from nanoDAQ.phase import loop_through_elink_phase, check_phase_scan


################################
# Command line argument parser #
################################

def parse_input(descr='Phase alignment helper for DCB+SALT.'):
    parser = ArgumentParser(description=descr)

    parser.add_argument('-g', '--gbt',
                        nargs='?',
                        type=int,
                        required=True,
                        help='''
specify GBT index.
                        ''')

    parser.add_argument('-s', '--slave',
                        nargs='?',
                        type=int,
                        required=True,
                        help='''
specify slave GBTx.
                        ''')

    parser.add_argument('-b', '--bus',
                        nargs='?',
                        type=int,
                        required=True,
                        help='''
specify I2C bus on slave GBTx that the ASIC is connected.
                        ''')

    parser.add_argument('-a', '--asic',
                        nargs='?',
                        type=int,
                        required=True,
                        help='''
specify ASIC.
                        ''')

    parser.add_argument('-c', '--channel',
                        nargs='?',
                        type=int,
                        required=True,
                        help='''
specify MiniDAQ channel.
                        ''')

    return parser


if __name__ == '__main__':
    parser = parse_input()
    args = parser.parse_args()

    opts_w()  # Enable memory monitoring options. (looping, etc.)
    fiber_w(args.channel)  # Select specified MiniDAQ channel.

    print('Current readings of MiniDAQ channel {}:'.format(args.channel))
    print_elink_table(mem_r()[-10:], style=alternating_color)

    daq_chs = input('Input elinks to be aligned, separated by space: ')
    daq_chs = list(map(int, daq_chs.split()))

    if len(daq_chs) > 5:
        raise ValueError("Too many elink channels! {} can't be coming from the same SALT!".format(
            ','.join(daq_chs)))

    print('Generating phase-scanning table...')
    phase_scan_raw = loop_through_elink_phase(args.gbt, args.slave, daq_chs)
    phase_scan_tab, phase_adj = check_phase_scan(phase_scan_raw)
    print(tabulate(phase_scan_tab, headers=['phase']+daq_chs,
          colalign=['left']+['right']*len(daq_chs)))
