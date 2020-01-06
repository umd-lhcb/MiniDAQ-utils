#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Jan 06, 2020 at 02:08 AM -0500

import sys

from collections import namedtuple
from tabulate import tabulate
from sty import fg

from nanoDAQ.utils import hex_pad, num_of_bit, bit_shift, most_common


################
# Elink basics #
################

ElinkDataFrame = namedtuple('ElinkDataFrame', ['tx_datavalid', 'header'] +
                            ['elk'+str(i) for i in range(13, -1, -1)])


def elink_parser(df):
    assert(len(df) == 16)

    # NOTE: the rightmost 2-Bytes are header
    tx_datavalid = df[-4]
    header = df[-3]
    elk_13_12 = df[-2:]

    elk_11_8 = df[-16:-12]
    elk_7_4 = df[-8:-4]
    elk_3_0 = df[-12:-8]

    elk_11_8 = df[-8:-4]
    elk_7_4 = df[-12:-8]
    elk_3_0 = df[-16:-12]

    return ElinkDataFrame(tx_datavalid, header, *elk_13_12,
                          *elk_11_8, *elk_7_4, *elk_3_0)


#######################
# Elink data checkers #
#######################

def check_tx_datavalid(data):
    return 1 if 0x80 == data else 0


def check_bit_shift(data, expected=0xc4):
    size = num_of_bit(hex_pad(expected))

    for shift in range(size):
        # We choose to shift DATA (This is chosen to make manipulating OUR
        # hardware more easily).
        if bit_shift(data, shift, size) == expected:
            return shift

    return -1


#############################
# Elink output highlighters #
#############################

def highlight_non_mode(data, mode):
    if data != mode:
        return (True, fg.blue + hex_pad(data) + fg.rs)
    else:
        return (False, hex_pad(data))


def highlight_chs(data, ch, chs):
    if ch in chs:
        return (True, fg.blue + hex_pad(data) + fg.rs)
    else:
        return (False, hex_pad(data))


def highlight_search_pattern(data, pattern):
    result = check_bit_shift(data, pattern)

    if result == 0:
        return (True, fg.green + hex_pad(data) + fg.rs)
    elif result > 0:
        return (True, fg.yellow + hex_pad(data) + fg.rs)
    else:
        return (False, hex_pad(data))


################
# Elink output #
################

def transpose(elk_df_lst):
    return {k: [getattr(d, k) for d in elk_df_lst]
            for k in ElinkDataFrame._fields}


def format_elink_table(elk_df_lst_t, indices):
    result = []

    for i in indices:
        row = []
        row.append(elk_df_lst_t['tx_datavalid'][i])
        row.append(elk_df_lst_t['header'][i])

        elk_13_12 = '-'.join([elk_df_lst_t['elk13'][i],
                              elk_df_lst_t['elk12'][i]])
        row.append(elk_13_12)

        for leading_ch in range(11, -1, -4):
            elks = [elk_df_lst_t['elk'+str(ch)][i]
                    for ch in range(leading_ch, leading_ch-4, -1)]
            row.append('-'.join(elks))

        result.append(row)

    return result


def print_elink_table(elk_df_lst,
                      highlighter=lambda x, y, z: highlight_non_mode(x, y),
                      highlighted_only=False):
    indices = []
    size = len(elk_df_lst)

    # Transpose elink data frames to each elink channel
    elk_df_lst_t = transpose(elk_df_lst)
    # For pipe output
    elk_df_lst_t_cp = {k: list(map(hex_pad, v))
                       for k, v in elk_df_lst_t.items()}

    # Find the mode for each field
    modes = {k: most_common(v)[0] for k, v in elk_df_lst_t.items()}

    # Apply highlight and matching
    for k, v in elk_df_lst_t.items():
        for i in range(0, size):
            is_styled, out = highlighter(v[i], modes[k], k)
            v[i] = out

            if highlighted_only and is_styled:
                indices.append(i)

    # Remove duplicated indices
    if highlighted_only:
        indices = sorted(set(indices))
    else:
        indices = list(range(size))

    # Generate output
    if sys.stdout.isatty():
        output = format_elink_table(elk_df_lst_t, indices)
    else:
        output = format_elink_table(elk_df_lst_t_cp, indices)

    try:
        print(tabulate(output,
                       headers=['tx_datavalid', 'header', '13-12', '11-8',
                                '7-4', '3-0'],
                       colalign=['right']*6))
    except IndexError:
        print('No highlighted row!')


#########################
# Elink data operations #
#########################

def elink_extract(elk_df_lst, names):
    result = {k: [] for k in names}

    for elk_df in elk_df_lst:
        for n in names:
            result[n].append(getattr(elk_df, n))

    return result


def elink_extract_chs(elk_df_lst, chs):
    names = ['elk'+str(ch) for ch in chs]
    return {int(k.replace('elk', '')): v
            for k, v in elink_extract(elk_df_lst, names).items()}
