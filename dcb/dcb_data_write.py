#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Oct 22, 2019 at 03:33 PM -0400

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


##################
# I2C operations #
##################

def i2c_write(gbt, sca, ch, slave, addr, val, mode=0, freq=3):
    size = num_of_byte(val)
    call([
        'i2c_op',
        '--size', size, '--val', is_hex(val),
        '--gbt', gbt, '--sca', sca,
        '--slave', slave, '--addr', addr,
        '--mode', mode, '--ch', ch, '--freq', freq,
        '--write'
    ])


def i2c_read(gbt, sca, ch, slave, addr, size, mode=0, freq=3):
    call([
        'i2c_op',
        '--size', size,
        '--gbt', gbt, '--sca', sca,
        '--slave', slave, '--addr', addr,
        '--mode', mode, '--ch', ch, '--freq', freq,
        '--read'
    ])


########
# Main #
########

if __name__ == '__main__':
    args = parse_input()

    for slave in SLAVE_ADDR:
        i2c_write(args.gbt, args.sca, slave, args.addr, args.val)

        # Read back the status
        status = i2c_read(args.gbt, args.sca, slave, '1AF', 1)
        print('Data GBTx #{} is in {} state'.format(slave, status))
