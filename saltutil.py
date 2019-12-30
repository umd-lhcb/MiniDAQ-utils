#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Dec 30, 2019 at 12:43 AM -0500

import sys

from argparse import ArgumentParser

from nanoDAQ.ut.salt import SALT, SALT_SER_SRC_MODE, SALT_TFC_VALID_PHASE
from nanoDAQ.utils import add_default_subparser, HexToIntAction


#################################
# Command line arguments parser #
#################################

def add_salt_default_subparser(*args, add_asics=True, **kwargs):
    cmd = add_default_subparser(*args, **kwargs)
    if add_asics:
        cmd.add_argument('-a', '--asics',
                         nargs='+',
                         type=int,
                         default=None,
                         help='''
    specify ASICs to be programmed.
    ''')

    return cmd


def parse_input(descr='SALT programming utility.'):
    parser = ArgumentParser(description=descr)
    parser.add_argument('bus',
                        type=int,
                        help='''
specify I2C bus (GPIO bus has the same index as I2C bus).''')

    cmd = parser.add_subparsers(dest='cmd')

    add_salt_default_subparser(cmd, 'init', description='''
initialize specified ASICs with default configuration.
    ''')

    ser_src_cmd = add_salt_default_subparser(cmd, 'ser_src', description='''
control serializer register.
''')
    ser_src_cmd.add_argument('src',
                             help='''
specify the serializer register value. supported shortcuts: {}.
    '''.format('|'.join(SALT_SER_SRC_MODE.keys())))

    write_cmd = add_salt_default_subparser(cmd, 'write', description='''
specify SALT address, register address and value to write.
''')
    write_cmd.add_argument('addr',
                           action=HexToIntAction,
                           help='''
specify SALT address.
''')
    write_cmd.add_argument('reg',
                           action=HexToIntAction,
                           help='''
specify SALT register address.
''')
    write_cmd.add_argument('val',
                           help='''
specify SALT register value.
''')

    read_cmd = add_salt_default_subparser(cmd, 'read', description='''
specify SALT address, register address and size to read.
''')
    read_cmd.add_argument('addr',
                          action=HexToIntAction,
                          help='''
specify SALT address.
''')
    read_cmd.add_argument('reg',
                          action=HexToIntAction,
                          help='''
specify SALT register address.
''')
    read_cmd.add_argument('size',
                          type=int,
                          help='''
specify number of registers to read.
''')

    reset_cmd = add_salt_default_subparser(cmd, 'reset', description='''
reset SALT.
''')
    reset_cmd.add_argument('final_state',
                           nargs='?',
                           const='high',
                           choices=['high', 'low'],
                           default='high',
                           help='''
specify the final state after pulling GPIO to low.''')

    phase_cmd = add_salt_default_subparser(cmd, 'phase', description='''
specify SALT elink phase.
''')
    phase_cmd.add_argument('phase',
                           help='''
specify the elink phase of SALT.''')

    tfc_phase_cmd = add_salt_default_subparser(cmd, 'phase', description='''
specify SALT TFC phase.
''')
    tfc_phase_cmd.add_argument('phase',
                               choices=SALT_TFC_VALID_PHASE,
                               help='''
specify the TFC phase of SALT. Valid phases: {}.'''.format('|'.join(SALT_TFC_VALID_PHASE))
                               )

    return parser


if __name__ == '__main__':
    parser = parse_input()
    args = parser.parse_args()

    if args.cmd:
        salt = SALT(args.gbt, args.bus)
    else:
        parser.print_help()
        sys.exit(1)

    if args.cmd == 'init':
        salt.init(args.asics)

    elif args.cmd == 'ser_src':
        salt.ser_src(args.src, args.asics)

    elif args.cmd == 'write':
        salt.write(args.addr, args.reg, args.val, args.asics)

    elif args.cmd == 'read':
        salt.read(args.addr, args.reg, args.size, args.asics)

    elif args.cmd == 'reset':
        salt.reset(args.final_state)

    elif args.cmd == 'phase':
        salt.phase(args.phase, args.asics)

    elif args.cmd == 'tfc_phase':
        salt.tfc_phase(args.phase, args.asics)
