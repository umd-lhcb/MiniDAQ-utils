#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Jan 17, 2020 at 03:31 AM -0500

from argparse import ArgumentParser, ArgumentTypeError
from tabulate import tabulate

from nanoDAQ.gbtclient.fpga_reg import mem_mon_read_safe as mem_r
from nanoDAQ.gbtclient.fpga_reg import mem_mon_fiber_write_safe as fiber_w
from nanoDAQ.gbtclient.fpga_reg import mem_mon_options_write_safe as opts_w

from nanoDAQ.utils import hex_pad
from nanoDAQ.elink import print_elink_table, highlight_chs

from nanoDAQ.phase import loop_phase_elk, scan_phase_elink
from nanoDAQ.phase import adj_dcb_elink_phase, adj_salt_elink_phase
from nanoDAQ.phase import salt_tfc_mode, adj_salt_tfc_phase


###########
# Helpers #
###########

def str2bool(v, error=ArgumentTypeError):
    if isinstance(v, bool):
        return v

    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise error('Boolean value expected.')


def input2bool(question):
    try:
        choice = input(question + ' [y/n]').lower()
        return str2bool(choice, ValueError)
    except ValueError:
        input2bool(question)


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

    parser.add_argument('-e', '--elinks',
                        nargs='+',
                        type=int,
                        default=None,
                        help='''
specify DCB elink channels.
                        ''')

    parser.add_argument('--non-verbose',
                        action='store_true',
                        help='''
don't print the memory monitoring after the phase adjustment.
                        ''')

    parser.add_argument('--adjust-elink-phase',
                        type=str2bool,
                        nargs='?',
                        const=True,
                        default=None,
                        help='''
specify if adjust elink phase.
                        ''')

    parser.add_argument('--adjust-tfc-phase',
                        type=str2bool,
                        nargs='?',
                        const=True,
                        default=None,
                        help='''
specify if adjust TFC phase.
                        ''')

    return parser


if __name__ == '__main__':
    parser = parse_input()
    args = parser.parse_args()

    opts_w()  # Enable memory monitoring options. (looping, etc.)
    fiber_w(args.channel)  # Select specified MiniDAQ channel.

    # Figure out elinks to be adjusted #########################################

    if args.elinks is None:
        salt_tfc_mode(args.gbt, args.bus, args.asic, mode='fixed')  # Set SALT to output fixed pattern

        print('Current readings of MiniDAQ channel {}:'.format(args.channel))
        print_elink_table(mem_r()[-10:])
        daq_chs = input('Input elinks to be aligned, separated by space: ')
        daq_chs = list(map(int, daq_chs.split()))

    else:
        daq_chs = args.elinks

    highlighter = lambda x, y, z: \
        highlight_chs(x, z, ['elk'+str(n) for n in daq_chs])
    print('Will adjust the following DCB elinks: {}'.format(
        ', '.join(map(str, daq_chs))
    ))

    # Adjust elink phase #######################################################

    if args.adjust_elink_phase is not None:
        elk_op = args.adjust_elink_phase
    else:
        elk_op = input2bool('Continue to elink phase adjustment?')

    if elk_op:
        print('Generating phase-scanning table, this may take awhile...')
        elk_scan_raw = loop_phase_elk(daq_chs, args.gbt, args.slave)
        elk_scan_tab, elk_adj, elk_pattern = scan_phase_elink(elk_scan_raw)
        print(tabulate(elk_scan_tab, headers=['phase']+daq_chs,
              colalign=['left']+['right']*len(daq_chs)))

        if len(elk_adj) == len(daq_chs):
            print('Current fixed pattern is {}, adjusting DCB and SALT phase...'.format(
                hex_pad(elk_pattern)))
            adj_dcb_elink_phase(elk_adj, args.gbt, args.slave)
            adj_salt_elink_phase(elk_pattern, args.gbt, args.bus, args.asic)
            success = True

    # Adjust TFC phase #########################################################

    if args.adjust_tfc_phase is not None:
        tfc_op = args.adjust_tfc_phase
    else:
        tfc_op = input2bool('Continue to TFC phase adjustment?')

    if tfc_op:
        salt_tfc_mode(args.gbt, args.bus, args.asic, mode='tfc')
        print('Tuning TFC phase, this may take awhile...')
        success = adj_salt_tfc_phase(daq_chs, args.gbt, args.bus, args.asic)

    # Print out memory to see adjust result ####################################

    if (not args.non_verbose) and success:
        print_elink_table(mem_r()[-10:], highlighter=highlighter)
