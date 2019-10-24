#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Oct 24, 2019 at 04:12 PM -0400

import re

from argparse import ArgumentParser
from subprocess import check_output
from itertools import zip_longest


################
# Configurable #
################
# NOTE: These must be strings

GBT = '5'
SCA = '0'
I2C_CH = '6'
SLAVE_ADDR = ['1', '2', '3', '4', '5', '6']

GBTX_STATES = {'61': 'Idle', '14': 'Pause for config'}


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

def chunk(iterable, size, padvalue=''):
    return map(''.join, zip_longest(*[iter(iterable)]*size, fillvalue=padvalue))


def validate_input(s):
    size = len(s) / 2 / 4
    if int(size) == size:
        return True
    else:
        return False


def read_file(path, padding=lambda x: '0'+x if len(x) == 1 else x):
    values = ''
    with open(path, 'r') as f:
        for line in f:
            values += padding(line.strip())

    return values


def is_hex(s):
    try:
        int(s, 16)
        return str(s)

    except ValueError:
        return read_file(s)


def parse_i2c_stdout(stdout, fields=[r'.*GBT Link : (0x\d+)',
                                     r'.*I2C Reading: (\d+)']):
    results = []
    stdout = stdout.replace('\n', '')  # Remove lines

    for pattern in fields:
        matched = re.match(pattern, stdout)
        if matched:
            results.append(matched.group(1))
        else:
            results.append('')

    return results


##################
# I2C operations #
##################

def i2c_activate_ch(gbt, sca, ch):
    check_output(['sca_test', '--gbt', gbt, '--sca', sca, '--activate-ch', ch])


def i2c_write(gbt, sca, ch, slave, addr, val, mode='0', freq='3'):
    stdout = []
    val = is_hex(val)

    if validate_input(val) or len(val)/2 == 366:
        for slice_addr, four_bytes in enumerate(chunk(val, 8),
                                                start=int(addr, 16)):
            four_bytes = ''.join(reversed(list(chunk(four_bytes, 2))))
            slice_addr = hex(slice_addr*4)[2:]

            slice_stdout = check_output([
                'i2c_op',
                '--size', '1', '--val', four_bytes,
                '--gbt', gbt, '--sca', sca,
                '--slave', slave, '--addr', slice_addr,
                '--mode', mode, '--ch', ch, '--freq', freq,
                '--write'
            ]).decode('utf-8')

            stdout.append(slice_stdout)

    return stdout


def i2c_read(gbt, sca, ch, slave, addr, size, mode='0', freq='3'):
    return check_output([
        'i2c_op',
        '--size', size,
        '--gbt', gbt, '--sca', sca,
        '--slave', slave, '--addr', addr,
        '--mode', mode, '--ch', ch, '--freq', freq,
        '--read'
    ]).decode('utf-8')


########
# Main #
########

if __name__ == '__main__':
    args = parse_input()
    i2c_activate_ch(args.gbt, args.sca, I2C_CH)

    for slave in SLAVE_ADDR:
        i2c_write(args.gbt, args.sca, I2C_CH, slave, args.addr, args.val)

        # Read back the status
        status = i2c_read(args.gbt, args.sca, I2C_CH, slave, '1AF', '1')
        gbtx_idx, gbtx_state = parse_i2c_stdout(status)
        try:
            gbtx_state = GBTX_STATES[gbtx_state]
        except KeyError:
            pass

        print('Data GBTx {} is in {} state.'.format(gbtx_idx, gbtx_state))
