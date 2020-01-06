#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Jan 06, 2020 at 01:56 AM -0500

from argparse import ArgumentParser

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe
from nanoDAQ.gbtclient.fpga_reg import mem_mon_fiber_read_safe, \
    mem_mon_fiber_write_safe
from nanoDAQ.gbtclient.fpga_reg import mem_mon_options_read_safe, \
    mem_mon_options_write_safe
from nanoDAQ.elink import print_elink_table, highlight_search_pattern, \
    highlight_non_mode
from nanoDAQ.utils import HexToIntAction


################################
# Command line argument parser #
################################

def parse_input(descr='Monitoring elinks.'):
    parser = ArgumentParser(description=descr)

    parser.add_argument('-s', '--search',
                        action=HexToIntAction,
                        default=None,
                        help='''
specify pattern to search
''')

    parser.add_argument('-H', '--highlight',
                        action='store_true',
                        help='''
show data frames with highlight only.
''')

    parser.add_argument('-n', '--num',
                        type=int,
                        default=1,
                        help='''
specify number of 256-frames to obtain.
''')

    parser.add_argument('-c', '--channel',
                        type=int,
                        default=None,
                        help='''
specify elink channel to read.
''')

    return parser


###########
# Aliases #
###########

read    = mem_mon_read_safe
fiber_r = mem_mon_fiber_read_safe
fiber_w = mem_mon_fiber_write_safe
opts_r  = mem_mon_options_read_safe
opts_w  = mem_mon_options_write_safe


if __name__ == '__main__':
    parser = parse_input()
    args = parser.parse_args()

    if args.channel:
        fiber_w(args.channel)

    readout = []
    for i in range(args.num):
        readout += read()

    if args.search:
        highlighter = lambda x, y, z: highlight_search_pattern(x, args.search)
    else:
        highlighter = lambda x, y, z: highlight_non_mode(x, y)

    print_elink_table(readout, highlighter, args.highlight)
