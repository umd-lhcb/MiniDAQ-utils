#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Wed Dec 18, 2019 at 02:48 AM -0500

from argparse import ArgumentParser

from nanoDAQ.ut.dcb import DCB
from nanoDAQ.ut.salt import SALT

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r
from nanoDAQ.gbtclient.fpga_reg import mem_mon_fiber_write_safe as fiber_w
from nanoDAQ.gbtclient.fpga_reg import mem_mon_options_write_safe as opts_w
from nanoDAQ.phase import print_elink_table, alternating_color


################################
# Command line argument parser #
################################

def parse_input(descr='Phase alignment helper for DCB+SALT.'):
    parser = ArgumentParser(description=descr)

    parser.add_argument('-g', '--gbt',
                        nargs='?',
                        type=int,
                        help='''
specify GBT index.
                        ''')

    parser.add_argument('-s', '--slave',
                        nargs='?',
                        type=int,
                        help='''
specify slave GBTx.
                        ''')

    parser.add_argument('-b', '--bus',
                        nargs='?',
                        type=int,
                        help='''
specify I2C bus on slave GBTx that the ASIC is connected.
                        ''')

    parser.add_argument('-a', '--asic',
                        nargs='?',
                        type=int,
                        help='''
specify ASIC.
                        ''')

    return parser


if __name__ == '__main__':
    parser = parse_input()
    args = parser.parse_args()

    # Initialize devices
    dcb = DCB(args.gbt)
    salt = SALT(args.gbt, args.bus)

    # Enable memory monitoring options (looping, etc.)
    opts_w()
