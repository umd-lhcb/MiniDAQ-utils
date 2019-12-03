#!/usr/bin/env python3
#
# Author: Yipeng Sun
# License: BSD 2-clause
# Last Change: Tue Dec 03, 2019 at 12:07 AM -0500


#############
# Constants #
#############

GBT_PREF = 'Gbt'
GBT_SERV = 'UMDlab'


###########
# Helpers #
###########

def fill(s, max_len=128, char='\0'):
    if len(s) > max_len:
        raise ValueError('{} is longer than max length {}.'.format(s, max_len))
    else:
        return s.ljust(max_len, char)
