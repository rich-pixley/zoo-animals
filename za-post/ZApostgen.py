#!/usr/bin/env python
# Time-stamp: <12-Jun-2012 16:18:43 PDT by rich.pixley@palm.com>

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

"""
This module is now a thin veneer over what amount to remote procedure
calls to the ZApostd daemon.  That is, this is a shell callable script
which implements the client side of those RPCs.  Or, if you prefer,
this script uplifts the RPCs into a shell callable API.

.. todo:: add python tests
"""

from __future__ import print_function, unicode_literals

__docformat__ = 'restructuredtext en'

import platform

if platform.python_version_tuple()[0] == "2":
    import ConfigParser as configparser
else:
    import configparser

import collections
import contextlib
import errno
import logging
import os
import socket
import sys
import time

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def ContextLog(logger, oline, cline):
    """
    ContextLog(logger, oline, cline)

    Tell'em what you're gonna do, do something, then tell them that
    you done it.
    """
    logger('{}...'.format(oline))
    yield
    logger('{}.'.format(cline))

class Connection(object):
    """
    This object is now the client side of a set of remote procedure
    calls to the ZApostd daemon.
    """

    __all__ = [
        'close',
        'down',
        'lock',
        'test',
        'unlock',
        'up',
        ]

    def __init__(self, unixdomainsocket=None, address=None, port=None):
        self.logger = logging.getLogger('{}.{}'.format(__name__, self.__class__.__name__))

        with ContextLog(self.logger.debug, 'initializing', 'initialized'):
            self.unixdomainsocket = unixdomainsocket
            self.address = address
            self.port = port

            if self.address is not None:
                af = socket.AF_INET
                addr = (self.address, self.port)
            else:
                af = socket.AF_UNIX
                addr = self.unixdomainsocket

            logger.debug('connecting on {}'.format(addr))
            self.socket = socket.socket(af, socket.SOCK_STREAM)

            sleepdur = 1
            while True:
                try:
                    self.socket.connect(addr)
                    break

                except socket.error as err:
                    if err.errno == errno.ECONNREFUSED:
                        logger.info('connection failed: {} - {}.  sleeping {}'.format(
                            err.errno, os.strerror(err.errno), sleepdur))
                        time.sleep(sleepdur)
                        sleepdur *= 2
                    else:
                        raise

            response = self.socket.recv(1024).decode('utf-8').strip()
            self.logger.debug('Received: {}'.format(response))

    def up(self):
        pass # hm.

    def down(self):
        self.logger.debug('Requesting daemon shutdown.')
        self.socket.send('shutdown\n'.encode('utf-8'))
        self.close()

    def close(self):
        with ContextLog(self.logger.debug, 'closing', 'closed'):
            self.socket.close()
            del self.socket

    def RPC(self, request):
        self.logger.debug('Requesting: {}'.format(request))
        self.socket.send('{}\n'.format(request))
        response = self.socket.recv(1024).decode('utf-8').strip()
        self.logger.debug('Received: {}'.format(response))
        return collections.deque(response.split())

    def clear_locks(self):
        """
        Clear all locks.
        """
        response = self.RPC('clear_locks')
        return list(response)

    def locks(self):
        """
        Return a list of outstanding locks.
        """
        response = self.RPC('locks')

        rettodo = response.popleft()
        assert rettodo == 'locks', rettodo

        return list(response)

    def test(self, lock):
        """
        Check whether *lock* is locked.  Returns True if so, False if
        not.  See ZApostd.py for locking semantics.
        """
        response = self.RPC('test {}'.format(lock))
        assert len(response) == 3, response

        rettodo = response.popleft()
        assert rettodo == 'test', rettodo

        retlock = response.popleft()
        assert retlock == lock, (retlock, lock)

        retret = response.popleft()
        retval = True if retret == 'True' else False
        assert not len(response), response
        return retval

    def lock(self, lock, pid):
        """
        Lock a lock named *lock* as though it were locked by the
        process with *pid*.  See ZApostd.py for locking semantics.
        """
        response = self.RPC('lock {} {}'.format(pid, lock))

        rettodo = response.popleft()
        assert rettodo == 'lock', x

        retpid = int(response.popleft())
        assert retpid == pid, (retpid, pid)

        retlock = response.popleft()
        assert retlock == lock, (retlock, lock)

        retret = response.popleft()
        retval = True if retret == 'True' else False
        assert not len(response), response
        return retval

    def unlock(self, lock, pid):
        """
        Attempt to unlock *lock* as though by *pid*.  See ZApostd.py for
        locking semantics.
        """
        response = self.RPC('unlock {} {}'.format(pid, lock))

        rettodo = response.popleft()
        assert rettodo == 'unlock', rettodo

        retpid = int(response.popleft())
        assert retpid == pid, (retpid, pid)

        retlock = response.popleft()
        assert retlock == lock, (retlock, lock)

        retret = response.popleft()
        retval = True if retret == 'True' else False
        assert not len(response)
        return retval

    def next(self, pid, count, requests):
        """
        Return the next component(s) to be tested.  *Requests* is a list
        of requested components.  *Pid* is the process id of the
        requesting process.  *Count* is a number of responses desired.
        """
        response = self.RPC('next ' + ' '.join([str(pid), str(count)] + requests))

        rettodo = response.popleft()
        assert rettodo == 'next', rettodo

        retpid = int(response.popleft())
        assert retpid == pid, (retpid, pid)

        retcount = int(response.popleft())
        assert retcount == count, (retcount, count)

        return list(response)

def getopts():
    import optparse

    u = ''
    u += 'usage: %prog\n'

    default_unixdomainsocket = 'zadc-socket'

    configs = configparser.ConfigParser()
    configs.read('/etc/za.conf')

    parser = optparse.OptionParser(usage = u)

    # General options
    general = optparse.OptionGroup(parser, 'General Options', '')

    general.add_option('-A', '--address', dest='address',
                       action='store', type='string', default=None,
                       help='connect to ZApostd on specified address.  (default: none')

    general.add_option('-C', '--clear-locks', dest='clear_locks',
                       action='store_true', default=False,
                       help='clear all outstanding locks.  (default: False)')

    general.add_option('-c', '--count', dest='count',
                       action='store', type='int', default=1,
                       help='produce this many answers.  (default: 1)')

    general.add_option('-H', '--homedir', dest='homedir',
                       action='store', type='string', default='',
                       help='operate with the specific home directory.  (default: ~)')

    general.add_option('-L', '--lock', dest='locks',
                       action='append', type='string', default=[],
                       help='lock the named arguments.  (default: lock only as necessary)')

    general.add_option('-l', '--logname', dest='logname',
                       action='store', type='string', default=os.getenv('LOGNAME', 'za-post'),
                       help='operate with the specific logname.  (default: LOGNAME from environment)')

    general.add_option('-n', '--component', dest='components',
                       action='append', type='string', default=[],
                       help='a component which should be tried before anything else.  (may be given multiple times)')

    general.add_option('-p', '--pid', dest='pid',
                       action='store', type='int', default=os.getppid(),
                       help='pid to be used for locks.  (default: pid of calling process)')

    general.add_option('-P', '--port', dest='port',
                       action='store', type='int', default=1962,
                       help='port on which to connect to ZApostd server.  (default: 1962)')

    general.add_option('-Q', '--quit', dest='quit',
                       action='store_true', default=False,
                       help='ask server to shutdown after processing.  (default: False)')

    general.add_option('-S', '--locks', dest='all_locks',
                       action='store_true', default=False,
                       help='ask for a list of outstanding locks.  (default: False)')

    general.add_option('-T', '--test', dest='tests',
                       action='append', type='string', default=[],
                       help='test named arguments as locks.  returns zero exit status if all tested are locked.  (default: test only as necessary)')

    general.add_option('-U', '--unlock', dest='unlocks',
                       action='append', type='string', default=[],
                       help='unlock the named arguments.  (default: unlock only as necessary)')

    general.add_option('-w', '--workdir', dest='workdir',
                       action='store', type='string', default=configs.get('za-post', 'workdir'),
                       help='operate with the specific workdir.  (default: {})'.format(configs.get('za-post', 'workdir')))

    general.add_option('-X', '--unixdomainsocket', dest='unixdomainsocket',
                       action='store', type='string', default='',
                       help='operate with the specific workdir.  (default: ~/workdir/{})'.format(default_unixdomainsocket))

    parser.add_option_group(general)

    # logging options
    logopt = optparse.OptionGroup(parser, 'Logging Options', '')

    logopt.add_option('-F', '--logfile', dest='logfile',
                       action='store', type='string', default='',
                       help='log to named logfile.  (default: no logging)')

    logopt.add_option('-v', '--loglevel', dest='loglevel',
                       action='store', type='string', default='info',
                       help='log level to log.  (default: info)')

    logopt.add_option('-x', '--trace', dest='trace',
                       action='store_true', default=False,
                       help='Log to standard out.  (default: False)')

    parser.add_option_group(logopt)

    options, args = parser.parse_args()

    if not options.homedir:
        options.homedir = os.path.expanduser('~{}'.format(options.logname))

    if not options.workdir:
        options.workdir = os.path.join(options.homedir, 'workdir')

    if not options.unixdomainsocket:
        options.unixdomainsocket = os.path.join(options.workdir, default_unixdomainsocket)

    return options, args

def setup_logs(options):
    logger = logging.getLogger(__name__)

    if options.trace or options.logfile:
        loglevel = getattr(logging, options.loglevel.upper())

        f = logging.Formatter('%(asctime)s %(filename)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

        if not os.path.isdir(options.workdir):
            os.makedirs(options.workdir)

        for l in [logger]:
            l.setLevel(loglevel)

        if options.trace:
            s = logging.StreamHandler()
            s.setLevel(loglevel)
            s.setFormatter(f)

            logging.getLogger('').addHandler(s)

        if options.logfile:
            fh = logging.FileHandler(options.logfile)
            fh.setLevel(loglevel)
            fh.setFormatter(f)

            logging.getLogger('').addHandler(fh)

    return logger

if __name__ == '__main__':
    progname = sys.argv[0]
    retval = True

    options, args = getopts()

    logger = setup_logs(options)

    connection = Connection(address=options.address,
                            port=options.port,
                            unixdomainsocket=options.unixdomainsocket)

    if options.clear_locks:
        connection.clear_locks()

    for lockit in options.locks:
        with ContextLog(logger.debug,
                        'Locking {}'.format(lockit),
                        'Locked {}'.format(lockit)):
            retval &= connection.lock(lockit, options.pid)

    tested = [connection.test(testit) for testit in options.tests]
    retval &= all(tested)

    for t, l in zip(options.tests, tested):
        logger.debug('{} -> {}'.format(t, l))

    for unlockit in options.unlocks:
        with ContextLog(logger.debug,
                        'Unlocking {}'.format(unlockit),
                        'Unlocked {}'.format(unlockit)):
            retval &= connection.unlock(unlockit, options.pid)

    if options.all_locks:
        for lock in connection.locks():
            print(lock)

    if not (options.all_locks
            or options.unlocks
            or options.locks
            or options.tests
            or options.clear_locks
            or options.quit):
        for component in connection.next(options.pid, options.count, options.components):
            logger.debug('Next: {}'.format(component))
            print(component)

    if options.quit:
        connection.down()
    else:
        connection.close()

    sys.exit(0 if retval else 1)

# eof
