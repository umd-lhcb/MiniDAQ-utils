#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Oct 22, 2019 at 07:03 AM -0400

from argparse import ArgumentParser
from subprocess import call


################
# Configurable #
################

GBT = 5
SCA = 0
I2C_CH = 6
SLAVE_ADDR = [1, 2, 3, 4, 5, 6]


#################################
# Command line arguments parser #
#################################

DESCR = '''
write to all data GBTxes.
'''


def parse_input(descr=DESCR):
    parser = ArgumentParser(description=descr)

    parser.add_argument('addr',
                        help='''
start of the address.''')

    parser.add_argument('val',
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


###########
# Helpers #
###########

def num_of_byte(s):
    return len(s) / 2


def read_file(path, padding=lambda x: '0'+x if len(x) == 1 else x):
    values = ''
    with open(path, 'r') as f:
        for line in f:
            values += padding(line.strip())

    return values


def is_hex(s):
    try:
        int(s, 16)
        return s

    except ValueError:
        return read_file(s)


def write(gbt, sca, ch, slave, addr, val, mode=0, freq=3):
    size = num_of_byte(val)
    call([
        'i2c_op',
        '--size', size, '--val', val,
        '--gbt', gbt, '--sca', sca,
        '--slave', slave, '--addr', addr,
        '--mode', mode, '--ch', ch, '--freq', freq,
        '--write'
    ])


########
# Main #
########

if __name__ == '__main__':
    args = parse_input()

    for slave in SLAVE_ADDR:
        write(args.gbt, args.sca, slave, args.addr, args.val)
