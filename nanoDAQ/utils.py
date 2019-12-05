#!/usr/bin/env python
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 05, 2019 at 03:43 AM -0500


def hex_pad(n):
    s = hex(n)[2:]
    if len(s) % 2 == 1:
        return '0'+s
    else:
        return s


def hex_rep(lst_of_num):
    return ''.join(map(hex_pad, lst_of_num))


def num_of_byte(hex_str):
    return len(hex_pad(hex_str)) / 2
