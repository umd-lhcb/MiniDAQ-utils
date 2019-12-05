#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Thu Dec 05, 2019 at 04:38 AM -0500

from argparse import ArgumentParser
from collections import defaultdict


###########
# Helpers #
###########

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


def dict_factory(known, default):
    d = defaultdict(lambda: default)
    d.update(known)
    return d


#######################
# Command line parser #
#######################

def parse_input(descr, parser=None):
    parser = ArgumentParser(description=descr) if parser is None else parser

    parser.add_argument('-g', '--gbt',
                        nargs='?',
                        type=int,
                        default=0,
                        help='''
specify GBT index.
''')

    parser.add_argument('--host',
                        nargs='?',
                        default='UMDlab',
                        help='''
specify GBT server hostname.
''')

    return parser
