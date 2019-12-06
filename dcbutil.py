#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Dec 06, 2019 at 01:07 AM -0500

import sys

from argparse import ArgumentParser, Action

from nanoDAQ.ut.dcb import DCB
from nanoDAQ.utils import add_default_subparser


#################################
# Command line arguments parser #
#################################

DESCR = '''
DCB utility. print current DCB status by default.
'''


class PRBSAction(Action):
    def __call__(self, parser, namespace, value, option_string=None):
        known_mode = {
            'on':  '03',
            'off': '00'
        }
        try:
            reg = known_mode[value]
        except KeyError:
            reg = value
        setattr(namespace, self.dest, reg)


class HexToIntAction(Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, int(value, base=16))


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
                          action=PRBSAction,
                          help='''
specify the PRBS register value. on|off supported.
    ''')

    write_cmd = add_default_subparser(cmd, 'write', description='''
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

    read_cmd = add_default_subparser(cmd, 'read', description='''
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

    add_default_subparser(cmd, 'status', description='''
print slave GBTxs status.
''')

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
        dcb.write(0x1c, args.mode, args.slaves)

    elif args.cmd == 'status':
        dcb.slave_status(args.slaves)

    elif args.cmd == 'write':
        dcb.write(args.reg, args.val, args.slaves)

    elif args.cmd == 'read':
        dcb.read(args.reg, args.size, args.slaves)
