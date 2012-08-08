#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2008 - 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals, print_function

"""
This module applies an old style bom submission to a bom file in
"oe/palm/conf/distro/nova-bom.inc" which is assumed to hold a nova
classic style bom.
"""

import os

import ZAbom

def getopts():
    import argparse

    parser = argparse.ArgumentParser(description='apply a submission.')

    parser.add_argument('requester')
    parser.add_argument('bomfile')
    parser.add_argument('speculation')

    options = parser.parse_args()

    if '<' in options.requester:
        # rip out requester email
        toss, toss, hold = options.requester.partition('<')
        options.requester, toss, toss = hold.rpartition('>')

    if options.speculation[0] == "'" and options.speculation[-1] == "'":
        options.speculation = options.speculation[1:-1]

    return options

if __name__ == '__main__':
    options = getopts()
    
    bom = ZAbom.bom(options.bomfile, dereference=False)
    owners = bom.speculate(options.speculation, options.requester)

    tmpfile = options.bomfile + '-new'
    bom.write(tmpfile)
    os.rename(tmpfile, options.bomfile)

    print(owners)
