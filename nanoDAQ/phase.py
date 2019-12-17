#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Dec 17, 2019 at 02:51 AM -0500

from collections import namedtuple
from sty import fg, bg
from tabulate import tabulate

from .utils import hex_pad


###################
# Elink utilities #
###################

ElinkDataFrame = namedtuple('ElinkDataFrame', ['tx_datavalid', 'header'] +
                            ['elk'+str(i) for i in range(14)])


def elink_parser(df):
    assert(len(df) == 16)

    # NOTE: the rightmost 2-Bytes are header
    tx_datavalid = df[-4]
    header = df[-3]
    elk_13_12 = df[-2:]

    elk_11_8 = df[-8:-4]
    elk_7_4 = df[-12:-8]
    elk_3_0 = df[-16:-12]

    return ElinkDataFrame(tx_datavalid, header, *elk_13_12, *elk_11_8, *elk_7_4,
                          *elk_3_0)


def alternating_color(s):
    result = ''

    for idx, i in enumerate(range(0, len(s), 2)):
        byte = s[i:i+2]
        if idx % 2 == 0:
            result += fg.li_white + byte + fg.rs
        else:
            result += bg.li_white + fg.black + byte + fg.rs + bg.rs

    return result


def print_elink_table(elk_df_lst, highlight=list(), style=lambda x: x):
    result = []

    for elk_df in elk_df_lst:
        df =  [style(elk_df.tx_datavalid), style(elk_df.header),
               style(''.join(elk_df[1:3]))]

        for i in range(3, len(elk_df), 4):
            grp = ''
            for j in range(i, i+4):
                elk_ch = 14 - j
                if elk_ch in highlight:
                    grp += fg.red + hex_pad(elk_df[j]) + fg.rs
                else:
                    grp += elk_df[j]
            df.append(style(grp))

        result.append(df)

    print(tabulate(result, headers=['tx_datavalid', 'header', '13-12', '11-8',
                                    '7-4', '3-0'],
                   colalign=['right']*5))
