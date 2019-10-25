#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Fri Oct 25, 2019 at 04:25 PM -0400

import re

from argparse import ArgumentParser
from subprocess import check_output


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
# A single SALT is controlled by 6 10-Byte registers (?). Programming multiple
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

def flatten(l):
    return l[0] if len(l) == 1 else l


# e.g. [1, 2, 3, 4] with step 3 -> [1, 2, 3], [2, 3, 4]
def enum_const_chunk_size(l, start=0, step=1):
    max = len(l)
    for i in range(0, max, step):
        # 'max' is already not a legit index.
        if i+step >= max:
            yield start+max-step, flatten(l[max-step:max])
            break

        else:
            yield start+i, flatten(l[i:i+step])


def split_str(s, parts=4):
    chunks, chunk_size = len(s), len(s) // parts
    return [s[i:i+chunk_size] for i in range(0, chunks, chunk_size)]


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


##################
# I2C operations #
##################

def i2c_activate_ch(gbt, sca, ch):
    check_output(['sca_test', '--gbt', gbt, '--sca', sca, '--activate-ch', ch])


def i2c_write(gbt, sca, ch, slave, addr, val, mode='1', freq='0'):
    stdout = []

    for slice_addr, four_bytes in enum_const_chunk_size(val, step=8):
        four_bytes = ''.join(reversed(split_str(four_bytes)))
        slice_addr = hex(slice_addr/2 + int(addr, 16))[2:]

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
    i2c_activate_ch(args.gbt, args.sca, args.ch)

    for asic_addr in ASIC_GROUPS[args.asic_group]:
        for slave, val in SALT_INIT_SEQ:
            slave = str(slave + asic_addr*10)
            i2c_write(args.gbt, args.sca, args.ch, slave, '0', val)
