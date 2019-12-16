#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Mon Dec 16, 2019 at 12:09 PM -0500

from collections import defaultdict
from argparse import Action
from multiprocessing import Pool

from .exceptions import ExecError


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


####################
# Segfault handler #
####################

def wrap_func(f, *args, **kwargs):
    try:
        return (True, f(*args, **kwargs))
    except Exception:
        return (False, None)


def run_in_proc(f, *args, **kwargs):
    process_pool = Pool(1)
    result = process_pool.apply_async(wrap_func, (f,)+args, kwargs).get()
    return result[0]


def exec_guard(f, *args, max_retry=3, **kwargs):
    trial = 0
    while trial < max_retry:
        status, ret = run_in_proc(f, *args, **kwargs)
        if status:
            return ret
    raise ExecError('Cannot execute {}!'.format(f.__name__))
