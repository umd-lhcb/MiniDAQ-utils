#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Sun Dec 08, 2019 at 08:11 PM -0500

from collections import defaultdict
from argparse import Action


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


def pad(s):
    if len(s) % 2 == 1:
        return '0'+s
    else:
        return s


def num_of_byte(hex_str):
    return len(pad(hex_str)) / 2


def dict_factory(known, default):
    d = defaultdict(lambda: default)
    d.update(known)
    return d


def chunks(lst, size=16):
    return [lst[i:i+size] for i in range(0, len(lst), size)]


#######################
# Command line parser #
#######################

def add_default_subparser(subparsers, name, description):
    cmd = subparsers.add_parser(name, description=description)
    cmd.add_argument('-g', '--gbt',
                     nargs='?',
                     type=int,
                     default=0,
                     help='''
specify GBT index.
''')

    return cmd


class HexToIntAction(Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, int(value, base=16))
