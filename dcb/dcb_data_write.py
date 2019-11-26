#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Nov 26, 2019 at 04:14 PM -0500

import re
import sys

from argparse import ArgumentParser
from subprocess import check_output
from time import sleep


################
# Configurable #
################
# NOTE: These must be strings

GBT = '0'
SCA = '0'
I2C_CH = '6'
SLAVE_ADDR = ['1', '2', '3', '4', '5', '6']

GBTX_STATES = {'61': 'Idle', '15': 'Pause for config'}


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
gbt address (fiber index).''')

    parser.add_argument('--sca',
                        nargs='?',
                        default=SCA,
                        help='''
sca index.''')

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


def read_file(path, padding=lambda x: '0'+x if len(x) == 1 else x):
    values = ''
    with open(path, 'r') as f:
        for line in f:
            values += padding(line.strip())

    return values


def is_hex(s, terminate_recursion=False):
    try:
        int(s, 16)
        return str(s)

    except ValueError:
        if not terminate_recursion:
            return is_hex(read_file(s), True)
        else:
            raise ValueError('Invalid input/file content: {}'.format(s))


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

def i2c_activate_ch(gbt, sca, ch, t=0.2):
    check_output(['sca_test', '--gbt', gbt, '--sca', sca, '--activate-ch', ch])
    sleep(t)


def i2c_write(gbt, sca, ch, slave, addr, val, mode='0', freq='3'):
    stdout = []
    val = is_hex(val)

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

        elif args.addr == 'bias_current':
            print('Bias current {} mA...'.format(args.val))
            if args.val == '5':
                i2c_write(args.gbt, args.sca, I2C_CH, slave, '37',
                          '87991988FFFF0400')
                i2c_write(args.gbt, args.sca, I2C_CH, slave, 'fd',
                          '7e730000')
                i2c_write(args.gbt, args.sca, I2C_CH, slave, '184',
                          'aabbffff')
            elif args.val == '6':
                i2c_write(args.gbt, args.sca, I2C_CH, slave, '37',
                          '87992588FFFF0400')
                i2c_write(args.gbt, args.sca, I2C_CH, slave, 'fd',
                          '7e730000')
                i2c_write(args.gbt, args.sca, I2C_CH, slave, '184',
                          'aabbffff')
            else:
                print('{} mA is not supported! Giving up')
                sys.exit(1)

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
