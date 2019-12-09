#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Sun Dec 08, 2019 at 09:21 PM -0500

from collections import namedtuple


ElinkDataFrame = namedtuple('ElinkDataFrame', ['header'] +
                            ['elk'+str(i) for i in range(14)])


def elink_parser(df):
    assert(len(df) == 16)

    # NOTE: the rightmost 3-Bytes are header
    header = df[-3:]

    return ElinkDataFrame(header, *df[:-3])  # Leftmost byte is elink 0
