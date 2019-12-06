#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Dec 06, 2019 at 12:13 AM -0500

from argparse import ArgumentParser

from nanoDAQ.ut.dcb import DCB
from nanoDAQ.utils import add_default_subparser


#################################
# Command line arguments parser #
#################################

DESCR = '''
DCB utility. print current DCB status by default.
'''


def parse_input(descr=DESCR):
    parser = ArgumentParser(description=descr)
    cmd = parser.add_subparsers(dest='cmd')

    init_cmd = add_default_subparser(cmd, 'init', description='''
initialize specified slave GBTxs with a configuration file.
    ''')
    init_cmd.add_argument('filepath',
                          help='''
path to GBTx config file.
    ''')

    gpio_cmd = add_default_subparser(cmd, 'gpio', description='''
GPIO status and reset.
''')
    gpio_cmd.add_argument('--reset',
                          nargs='+',
                          type=int,
                          default=None,
                          help='''
specify GPIO lines to reset. default to print out current value of GPIO 0-6.
    ''')

    prbs_cmd = add_default_subparser(cmd, 'prbs', description='''
control PRBS register.
''')
    prbs_cmd.add_argument('mode',
                          help='''
specify the PRBS register value. on|off supported.
    ''')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_input()
    dcb = DCB(args.gbt)

    if args.cmd == 'init':
        dcb.init(args.filepath, args.slaves)

    elif args.cmd == 'gpio':
        if args.reset is not None:
            dcb.gpio_reset(args.reset)
        else:
            dcb.gpio_status()

    elif args.cmd == 'prbs':
        if args.mode == 'on':
            dcb.write(0x1c, '03', args.slaves)
        elif args.mode == 'off':
            dcb.write(0x1c, '00', args.slaves)
        else:
            dcb.write(0x1c, args.mode, args.slaves)

    else:
        dcb.slave_status()
