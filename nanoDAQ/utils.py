#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Wed Dec 18, 2019 at 02:18 AM -0500

from collections import defaultdict, Counter
from argparse import Action
from multiprocessing import Pool

from .exceptions import ExecError


###########
# Helpers #
###########

def pad(s, fmt=lambda x: x):
    s = fmt(s)
    return '0'+s if len(s) % 2 == 1 else s


def hex_pad(n):
    return pad(n, fmt=lambda x: hex(x)[2:])


def bin_pad(n, size=8):
    return bin(n)[2:].rjust(size, '0')


def hex_rep(lst_of_num):
    return ''.join(map(hex_pad, lst_of_num))


def num_of_byte(hex_str):
    return int(len(pad(hex_str)) / 2)


def num_of_bit(hex_str):
    return num_of_byte(hex_str) * 8


def dict_factory(known, default):
    d = defaultdict(lambda: default)
    d.update(known)
    return d


def chunks(lst, size=16):
    return [lst[i:i+size] for i in range(0, len(lst), size)]


def bit_shift(n, shift, size=8):
    s = bin_pad(n, size=size)
    return int(''.join([s[shift:size], s[0:shift]]), base=2)


def most_common(lst):
    data = Counter(lst)
    mc = max(lst, key=data.get)
    return (mc, data[mc])


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


#####################
# Run in subprocess #
#####################

def maybe(f, *args, **kwargs):
    try:
        return (True, f(*args, **kwargs))
    except Exception as e:
        return (False, e)


def run_in_proc(f, pool, *args, **kwargs):
    return pool.apply_async(maybe, (f,)+args, kwargs).get()


def exec_guard(f, *args, max_retry=3, **kwargs):
    trial = 0
    pool = Pool(1)

    while trial < max_retry:
        status, ret = run_in_proc(f, pool, *args, **kwargs)
        if status:
            pool.close()
            pool.join()
            return ret
        else:
            trial += 1

    pool.close()
    pool.join()
    raise ExecError('Cannot execute {}! The raw exception is {}: {}'.format(
        f.__name__, ret.__class__.__name__, str(ret)))
