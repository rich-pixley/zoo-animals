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
This module creates a shell callable interface to a work queue,
currently represented by a gdbm file.  The keys are unicode dates...
"""

import contextlib
import datetime
import email
import email.message
import email.parser
import os
import shelve
import socket
import sys

trace = False

class Work(object):
    def __init__(self, frm=None, validation=False, releasenotes=None):
        self.frm = frm
        self.validation = validation
        self.releasenotes = releasenotes

    def __repr__(self):
        return '{}(frm=\'{}\', validation=\'{}\', releasenotes=\'{}\')'.format(
            self.__class__.__name__, self.frm, self.validation, self.releasenotes)

    def comment(self):
        raise NotImplementedError

class Incremental(Work):
    pass

class Full(Work):
    pass

class Submission(Work):
    def __init__(self, frm=None, validation=False, releasenotes=None, submission=None):
        Work.__init__(self, frm=frm, validation=validation, releasenotes=releasenotes)
        self.submission = submission.strip()

    def __repr__(self):
        return 'Submission(frm=\'{}\', validation=\'{}\', releasenotes=\'{}\', submission=\'{}\')'.format(
            self.frm, self.validation, self.releasenotes, self.submission)

    def comment(self):
        retlist = []
        changes = self.submission.split()

        for verb, code in [('added to bom', '{'),
                           ('removed from bom', '}'),
                           ('moved to category {}', '+'),
                           ('granted to owner {}', '@'),
                           ('upgraded to version {}', '#'),
                           ('updated to submission {}', '=')]:
            retlist += [('component {}'+verb).format(component, destination)
                        for component, toss, destination in [c.partition(code)
                                                             for c in changes if code in c]]

        return ('\n'.join(retlist)
                + '\n\non behalf of {} from {}\n\n'.format(self.frm, socket.getfqdn())
                + self.releasenotes)


class SubmissionRequest(email.message.Message):
    releasenotes = ''
    updates = []
    movements = []

    def as_string(self):
        l = []
        l.extend(self.movements)
        l.extend(self.updates)

        result = ''
        if l:
            result += 'submission: {}\n'.format(' '.join(l))

        result += 'releasenotes: {}\n'.format(self.releasenotes)

        self.set_payload(result)

        return email.message.Message.as_string(self)

class SubmissionParser(email.parser.Parser):
    def __init__(self):
        email.parser.Parser.__init__(self, SubmissionRequest)

    def parse(self, file):
        parsed = email.parser.Parser.parse(self, file)

        if parsed.is_multipart():
            raise Exception('MIME confuses me')

        # read off any white space
        payload = parsed.get_payload()

        # submission is mandatory, validation is optional
        
        early, toss, rest = payload.partition('submission:')

        toss, toss, validation = early.partition('validation:')
        validation = validation.strip() in ['true', 'True', 'yes', 'Yes']
        validation = True if validation else False

        submission, toss, releasenotes = rest.partition('releasenotes:')
        submission = submission.strip()

        return Submission(frm=parsed['from'],
                          validation=validation,
                          submission=submission,
                          releasenotes=releasenotes)

def submission_from_file(file):
    return SubmissionParser().parse(file)

def getopts():
    import argparse

    parser = argparse.ArgumentParser(description='Manage work queue.')

    default_logname = os.getenv('LOGNAME', 'zoo-animals')    

    parser.add_argument('keys', nargs='*')

    parser.add_argument('-c', '--count', type=int, default=0, help='limit to this many')

    parser.add_argument('-d', '--database',
                        help='use a specific database. (default: WORKDIR/work)')

    parser.add_argument('-D', '--delete', metavar='KEY', action='append', help='delete KEY')

    parser.add_argument('--dump', action='store_true')

    parser.add_argument('-F', '--priority-full', action='store_true',
                        help='enter a request for a full build into the head of the queue')
    parser.add_argument('-f', '--force-full', action='store_true',
                        help='enter a request for a full build into the queue')
    
    parser.add_argument('-H', '--homedir', default='',
                        help='set home directory. (default: ~LOGNAME)')

    parser.add_argument('-I', '--priority-incremental', action='store_true',
                        help='enter a request for an incremental build into the head of the queue')
    parser.add_argument('-i', '--force-incremental', action='store_true',
                        help='enter a request for an incremental build into the queue')

    parser.add_argument('-j', '--just-keys', action='store_true',
                        help='list the keys currently in the database')

    parser.add_argument('-l', '--logname', default=default_logname,
                        help='set LOGNAME. (default: {})'.format(default_logname))

    parser.add_argument('--print-count', action='store_true')
    parser.add_argument('--print-comment', action='store_true')
    parser.add_argument('--print-releasenotes', action='store_true')
    parser.add_argument('--print-requester', action='store_true')
    parser.add_argument('--print-submission', action='store_true')
    parser.add_argument('--print-validation', action='store_true')

    parser.add_argument('-Q', '--init', action='store_true',
                        help='initialize a fresh database')

    parser.add_argument('-R', '--reorganize', action='store_true')

    parser.add_argument('-r', '--requester', action='store_true')

    parser.add_argument('-s', '--submission', nargs='?', action='append', type=argparse.FileType('r'), default=[],
                        help='add SUBMISSION')

    parser.add_argument('-w', '--workdir', default='',
                        help='specify a WORKDIR. (default: HOMEDIR/workdir)')

    parser.add_argument('-x', '--trace', action='store_true')

    options = parser.parse_args()

    if not options.homedir:
        options.homedir = os.path.expanduser('~{}'.format(options.logname))

    if not options.workdir:
        options.workdir = os.path.join(options.homedir, 'workdir')

    if not options.database:
        options.database = os.path.join(options.workdir, 'work')

    return options

# It's important that this date sort to earlier than anything else
# that might be in the queue.
ASAP = datetime.datetime(datetime.MINYEAR, 1, 1).isoformat()

def timestamp():
    return datetime.datetime.now().isoformat()

if __name__ == '__main__':
    options = getopts()
    
    if options.trace:
        trace = True

    gdbmflags = 'n' if options.init else 'w'

    with contextlib.closing(shelve.open(options.database, gdbmflags)) as shelf:

        if options.delete:
            for i in options.delete:
                for j in i.split():
                    del shelf[j]

        if options.submission:
            for submission in options.submission:
                shelf[timestamp()] = submission_from_file(submission)

        if options.reorganize:
            db.reorganize()

        if options.force_full:
            shelf[timestamp()] = Full()

        if options.force_incremental:
            shelf[timestamp()] = Incremental()

        if options.priority_full:
            shelf[ASAP] = Full()

        if options.priority_incremental:
            shelf[ASAP] = Incremental()

        if not options.keys:
            options.keys = sorted(shelf.keys())

        if not options.count:
            options.count = len(options.keys)

        if options.print_count:
            print(len(options.keys))

        else:
            for c, key in zip(range(options.count), options.keys):
                if options.just_keys:
                    print(key)

                elif options.print_requester:
                    print(shelf[key].frm)

                elif options.print_submission:
                    print(shelf[key].submission)

                elif options.print_validation:
                    print(shelf[key].validation)

                elif options.print_releasenotes:
                    print(shelf[key].releasenotes)

                elif options.print_comment:
                    print(shelf[key].comment())

                elif options.dump:
                    print('Key: {}'.format(key))
                    print('Data: {}'.format(shelf[key]))
                    print()

                else:
                    pass
