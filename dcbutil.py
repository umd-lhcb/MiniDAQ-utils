#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 05, 2019 at 05:29 AM -0500

from nanoDAQ.ut.dcb import DCB
from nanoDAQ.utils import parse_input as proto_parse_input


#################################
# Command line arguments parser #
#################################

DESCR = '''
DCB utility.
'''


def parse_input(descr=DESCR):
    parser = proto_parse_input(descr)

    parser.add_argument('-s', '--slaves',
                        nargs='+',
                        type=int,
                        default=None)

    cmd = parser.add_subparsers(dest='cmd')

    init_cmd = cmd.add_parser('init', description='''
initialize specified slave GBTxs with a configuration file.
''')
    init_cmd.add_argument('filepath',
                          help='''
path to GBTx config file.
    ''')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_input()
    dcb = DCB(args.gbt)

    if args.cmd == 'init':
        dcb.init(args.filepath, args.slaves)
