#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Oct 25, 2019 at 04:30 AM -0400

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

ASIC_GROUPS = {'west': range(4), 'east': range(4, 8)}
ASIC_GROUP_NAMES = tuple(ASIC_GROUPS.keys())

FIXED_PATTERN = 'f0'


#################################
# SALT initialization directive #
#################################
# A single SALT is controlled by 3 10-Byte registers (?). Programming multiple
# SALTs just means providing different initial addresses (0, 10, 20, etc.).

def salt_reg_gen(reg=['00']*10):
    def inner(addr, val):
        reg[addr] = val
        return ''.join(reg)
    return inner


salt0 = salt_reg_gen()
salt3 = salt_reg_gen()
salt5 = salt_reg_gen()


SALT_INIT_SEQ = [
    (0, salt0(4, '8c')),
    (0, salt0(6, '15')),
    (0, salt0(4, 'cc')),
    (0, salt0(0, '22')),
    (0, salt0(1, FIXED_PATTERN)),
    (0, salt0(8, '01')),
    (3, salt3(0, '24')),
    (3, salt3(1, '32')),
    (3, salt3(0, 'e4')),
    (0, salt0(2, '0f')),
    (0, salt0(3, '4c')),
    (5, salt5(7, '01')),
]


#################################
# Command line arguments parser #
#################################

DESCR = '''
write to a single 4-ASIC group (west/east).
'''


def parse_input(descr=DESCR):
    parser = ArgumentParser(description=descr)

    parser.add_argument('ch',
                        help='''
i2c channel of SALT.''')

    parser.add_argument('--asic-group',
                        nargs='?',
                        choices=ASIC_GROUP_NAMES,
                        default=ASIC_GROUP_NAMES[0],
                        help='''
choose between 4-ASIC group: {}.'''.format(', '.join(ASIC_GROUP_NAMES)))

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

    parser.add_argument('--fixed-pattern',
                        nargs='?',
                        default=FIXED_PATTERN,
                        help='''
set fixed pattern for 4-ASIC output.''')

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


def parse_i2c_stdout(stdout, fields=[r'.*Slave : (0x\d+)',
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


def enumerate_step(l, start=0, step=1):
    for i in l:
        yield start, i
        start += step


##################
# I2C operations #
##################

def i2c_activate_ch(gbt, sca, ch):
    check_output(['sca_test', '--gbt', gbt, '--sca', sca, '--activate-ch', ch])


def i2c_write(gbt, sca, ch, slave, addr, val, mode='1', freq='0'):
    stdout = []
    val = is_hex(val)

    if len(val)/2 == 366 or validate_input(val):
        for slice_addr, four_bytes in enumerate_step(
                chunk(val, 8), start=int(addr, 16), step=4):
            four_bytes = ''.join(reversed(list(chunk(four_bytes, 2))))
            slice_addr = hex(slice_addr)[2:]

            slice_stdout = check_output([
                'i2c_op',
                '--size', '1', '--val', four_bytes,
                '--gbt', gbt, '--sca', sca,
                '--slave', slave, '--addr', slice_addr,
                '--mode', mode, '--ch', ch, '--freq', freq,
                '--write'
            ]).decode('utf-8')

            stdout.append(slice_stdout)

    else:
        raise ValueError('Invalid input: \n{}'.format(val))

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
        if args.addr == 'prbs':
            print('PRBS {}...'.format(args.val))
            if args.val == 'on':
                i2c_write(args.gbt, args.sca, I2C_CH, slave, '1c', '03151515')
            elif args.val == 'off':
                i2c_write(args.gbt, args.sca, I2C_CH, slave, '1c', '00151515')
            else:
                i2c_write(args.gbt, args.sca, I2C_CH, slave, '1c', args.val)

        else:
            i2c_write(args.gbt, args.sca, I2C_CH, slave, args.addr, args.val)

        # Read back the status
        status = i2c_read(args.gbt, args.sca, I2C_CH, slave, '1AF', '1')
        gbtx_idx, gbtx_state = parse_i2c_stdout(status)
        try:
            gbtx_state = GBTX_STATES[gbtx_state]
        except KeyError:
            pass

        print('Data GBTx {} is in {} state.'.format(gbtx_idx, gbtx_state))
