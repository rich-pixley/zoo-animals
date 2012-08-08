#!/usr/bin/env python
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

# usage: %prog file [ file [ file [...]]]

# This script merges the timing data from several files into a single
# aggregate which is sent to stdout.

class stamp:
    def __init__(this, time, weight):
        this.time = long(time)
        this.weight = long(weight)

    def weighted_time(this):
        return this.time * this.weight

def minimum(x, y):
    if x < y:
        return x
    else:
        return y

def maximum(x, y):
    if x > y:
        return x
    else:
        return y

class timing_file:
    def __init__(this, filename = ''):
        this.stamps = {}
        this.filename = ''

        this.filename = filename

        if this.filename:
            f = open(filename, 'r')
            this.lines = f.readlines()
            f.close()
            this.lines = [ line.strip() for line in this.lines ]

            for line in this.lines:
                space_sep = line.split()
                if len(space_sep) != 2:
                    raise Exception('bad timing line in %s: %s' % (this.filename, line))

                star_sep = space_sep[0].split('*')
                if len(star_sep) == 1:
                    weight = 1
                else:
                    weight = star_sep[1]

                this.stamps[space_sep[1]] = stamp(star_sep[0], weight)

    def write(this):
        for stamp in this.stamps:
            print '%d*%d %s' % (this.stamps[stamp].time, this.stamps[stamp].weight, stamp)

    def merge(this, old):
        new = timing_file()
        minmax = ['maximum', 'minimum']

        for s in this.stamps:
            if s in minmax:
                continue

            if s in old.stamps:
                total_weight = this.stamps[s].weight + old.stamps[s].weight
                weighted_average_time = (this.stamps[s].weighted_time() + old.stamps[s].weighted_time()) / total_weight

                new.stamps[s] = stamp(weighted_average_time, total_weight)
            else:
                new.stamps[s] = this.stamps[stamp]

        for s in old.stamps:
            if s in minmax:
                continue

            if s not in this.stamps:
                new.stamps[s] = old.stamps[s]

        stamps = [this.stamps[s].time for s in this.stamps] + [old.stamps[s].time for s in old.stamps]

        new.stamps['maximum'] = stamp(reduce(maximum, stamps, 0), 0)
        if new.stamps['maximum'] > 0:
            new.stamps['minimum'] = stamp(reduce(minimum, stamps, new.stamps['maximum'].time), 0)

        return new

def option_parser():
    import optparse

    usage = "Usage: %prog file [ file [ file [...]]]"

    parser = optparse.OptionParser(usage = usage)

    general = optparse.OptionGroup(parser, 'General Options', '')

#     general.add_option('-i', '--input',
#                        type = 'string',
#                        dest = 'infile',
#                        default = '',
#                        help = 'use this as the input file [default: stdin]')

    parser.add_option_group(general)

    return parser

if __name__ == '__main__':
    import optparse

    options, args = option_parser().parse_args()

    sum = timing_file()

    for a in args:
        sum = sum.merge(timing_file(a))

    sum.write()
        
