#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Dec 06, 2019 at 05:22 AM -0500

import sys

from argparse import ArgumentParser

from nanoDAQ.ut.dcb import DCB
from nanoDAQ.utils import add_default_subparser, HexToIntAction


#################################
# Command line arguments parser #
#################################

def add_dcb_default_subparser(*args, add_slave=True, **kwargs):
    cmd = add_default_subparser(*args, **kwargs)
    if add_slave:
        cmd.add_argument('-s', '--slaves',
                         nargs='+',
                         type=int,
                         default=None,
                         help='''
    specify slave GBTxs to be programed.
    ''')

    return cmd


def parse_input(descr='DCB programming and controlling utility.'):
    parser = ArgumentParser(description=descr)
    cmd = parser.add_subparsers(dest='cmd')

    init_cmd = add_dcb_default_subparser(cmd, 'init', description='''
initialize specified slave GBTxs with a configuration file.
    ''')
    init_cmd.add_argument('filepath',
                          help='''
path to GBTx config file.
    ''')

    gpio_cmd = add_dcb_default_subparser(cmd, 'gpio', description='''
GPIO status and reset.
''', add_slave=False)
    gpio_cmd.add_argument('--reset',
                          nargs='+',
                          type=int,
                          default=None,
                          help='''
specify GPIO lines to reset. default to print out current value of GPIO 0-6.
    ''')

    prbs_cmd = add_dcb_default_subparser(cmd, 'prbs', description='''
control PRBS register.
''')
    prbs_cmd.add_argument('mode',
                          help='''
specify the PRBS register value. supported shortcuts: {}.
    ''')

    write_cmd = add_dcb_default_subparser(cmd, 'write', description='''
specify GBTx register address and value to write.
''')
    write_cmd.add_argument('reg',
                           action=HexToIntAction,
                           help='''
specify GBTx register address.
''')
    write_cmd.add_argument('val',
                           help='''
specify GBTx register value.
''')

    read_cmd = add_dcb_default_subparser(cmd, 'read', description='''
specify GBTx register address and size to read.
''')
    read_cmd.add_argument('reg',
                          action=HexToIntAction,
                          help='''
specify GBTx register address.
''')
    read_cmd.add_argument('size',
                          type=int,
                          help='''
specify number of registers to read.
''')

    add_dcb_default_subparser(cmd, 'status', description='''
print slave GBTxs status.
''')

    reset_cmd = add_dcb_default_subparser(cmd, 'reset', description='''
reset slave GBTxs.
''')
    reset_cmd.add_argument('final_state',
                           nargs='?',
                           const='high',
                           choices=['high', 'low'],
                           default='high',
                           help='''
specify the final state after pulling GPIO to low.''')

    return parser


if __name__ == '__main__':
    parser = parse_input()
    args = parser.parse_args()

    if args.cmd:
        dcb = DCB(args.gbt)
    else:
        parser.print_help()
        sys.exit(1)

    if args.cmd == 'init':
        dcb.init(args.filepath, args.slaves)

    elif args.cmd == 'gpio':
        if args.reset is not None:
            dcb.gpio_reset(args.reset)
        else:
            dcb.gpio_status()

    elif args.cmd == 'prbs':
        dcb.prbs(args.mode, args.slaves)

    elif args.cmd == 'status':
        dcb.slave_status(args.slaves)

    elif args.cmd == 'write':
        dcb.write(args.reg, args.val, args.slaves)

    elif args.cmd == 'read':
        dcb.read(args.reg, args.size, args.slaves)

    elif args.cmd == 'reset':
        dcb.reset(args.final_state)
