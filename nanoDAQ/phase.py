#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Dec 17, 2019 at 03:16 AM -0500

from collections import namedtuple
from sty import fg, bg
from tabulate import tabulate

from .utils import hex_pad


###################
# Elink utilities #
###################

ElinkDataFrame = namedtuple('ElinkDataFrame', ['tx_datavalid', 'header'] +
                            ['elk'+str(i) for i in range(13, -1, -1)])


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
        elk_df = ElinkDataFrame(*map(hex_pad, elk_df))
        df =  [style(elk_df.tx_datavalid), style(elk_df.header),
               style(''.join([elk_df.elk13, elk_df.elk12]))]

        for leading_ch in range(11, -1, -4):
            grp = ''
            for ch in range(leading_ch, leading_ch-4, -1):
                ch_data = getattr(elk_df, 'elk'+str(ch))
                if ch in highlight:
                    grp += fg.red + ch_data + fg.rs
                else:
                    grp += ch_data
            df.append(style(grp))

        result.append(df)

    print(tabulate(result,
                   headers=['tx_datavalid', 'header', '13-12', '11-8',
                            '7-4', '3-0'],
                   colalign=['right']*6))
