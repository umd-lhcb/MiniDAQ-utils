#!/usr/bin/env python2
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Oct 21, 2019 at 05:59 PM -0400

from argparse import ArgumentParser


################
# Configurable #
################

GBT = 5
SCA = 0
SLAVE_ADDR = [1, 2, 3, 4, 5, 6]


#################################
# Command line arguments parser #
#################################

DESCR = '''
write to all data GBTxes.
'''


def parse_input(descr=DESCR):
    parser = ArgumentParser(description=descr)

    parser.add_argument('start_address',
                        help='''
start of the address.''')

    parser.add_argument('value',
                        help='''
value to write. can be either hex values or path to file.''')

    parser.add_argument('--gbt',
                        nargs='?',
                        default=GBT,
                        help='''
gbt address (fiber index)''')

    parser.add_argument('--sca',
                        nargs='?',
                        default=SCA,
                        help='''
sca index.''')

    return parser.parse_args()


##########
# Helper #
##########

def num_of_byte(s):
    return len(s) / 2


def read_file(path, padding=lambda x: '0'+x if len(x) == 1 else x):
    values = []
    with open(path, 'r') as f:
        for line in f:
            values.append(padding(line))

    return values


def is_hex(s):
    try:
        int(s, 16)
        return s

    except ValueError:
        return read_file(s)
