#!/usr/bin/env /usr/bin/python
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
This script implements a daemon.  It has two sets of service
functionality combined.

The first and more primal set is that of a lock manager.  In this
implementation, locks are arbitrary strings managed by this daemon.
Clients connect, request a lock, receive it, and go on about their
lives.

The second and more abstract functionality is that of a gamma
function.  In artificial intelligence, a gamma function is a function
which produces a list of the potential next moves for a game player
which can then be evaluated.  In this case, the 'next move' is a
component to be checked in the search for errors.

As the post-commit checker runs, each thread connects to this daemon,
asks what should be done next, and then does that thing.  There are a
number of wins to having this information centrally located and
dynamically monitored rather than forcing each thread to read and
digest the data each cycle.

Version 1 heuristics in order...

#. anything named on the command line takes precedence
#. any 'bumped' components are high priority
#. any 'new' component is immediate game
#. the component least recently checked should be checked next

Protocol
--------

The protocol here is very simple.  Upon receiving a connection, the
server sends an ID string.  The ID string is purely decorative.  After
the ID string, the client sends 1-liner requests to which the server,
(eventually), responds with 1-liner responses.  This is all basic RPC
style.

:request: shutdown
:response: no response.  server simply shuts down.

Requests that the server shut down.

:request: test *lock*
:respose: test *lock* *result*

Check whether *lock* is locked.  *Result* is True if so, False if not.

:request: lock *pid* *lock*
:respose: lock *pid* *lock* *boolean*

Claim *lock* as though it were locked by the process with *pid*.

* *lock* is any arbitrary string, (no spaces).  I'm conventionally
  using a *partition*:*lock* structure in order to create multiple
  name spaces.

* *partition* represents a name space for locks. Currently used name
  spaces are 'channel' and 'component'. The previously used 'oedir'
  partition is not currently needed or used. As ZApostd is the only user
  of the oedir, no locking is necessary.

Here are the locking semantics.

- If a lock is not held, it can be locked.

- If a lock is held by the same pid then we assume that we're
  relocking our own lock and the locking attempt will be successful.

- If a lock is held by another pid and that pid is still in the
  process table then we assume that the lock is still valid and the
  locking attempt will fail.

- If a lock is held by another pid and that pid is no longer in the
  process table then we assume that the lock is stale and steal it.

:request: unlock *pid* *lock*
:respose: unlock *pid* *lock* *boolean*

Attempt to unlock *lock* as though by *pid*.

Here are the unlocking semantics:

- Only the locking pid may unlock.  Other attempts fail.  There should
  be no need to unlock someone else's lock since it's either valid or
  it can be stolen by a basic locking attempt.

- If the lock doesn't exist, unlocking it will be successful.

:request: locks
:response: locks [*lock* [*lock* ...]]

Return a list of outstanding locks.

:request: clear_locks
:response: clear_locks

Requests that all locks be cleared.  This is not intended for routine
use but has been important for test development.

:request: next *pid* *count* [*request* [*request* ...]]
:response: next *pid* *count* [*response* [*response* ...]]

Return the next *count* component(s) to be tested by *pid*.


Notes
-----

.. todo:: service ports are antiquated.  Zeroconf/bonjour/avahi can
          allocate them dynamically.

.. todo:: will need to lock oedir if we move to multiple threads.

.. todo:: should check subversion before reloading.

.. todo:: should watch svnlocfile and reload on change.
"""

import platform

if platform.python_version_tuple()[0] == "2":
    import ConfigParser as configparser
else:
    import configparser

import collections
import contextlib
import glob
import grp
import itertools
import logging
import optparse
import os
import psutil
import pwd
import socket
import sys
import time

if sys.version_info.major <= 2:
    import SocketServer as socketserver
else:
    import socketserver

import pysvn

sys.path.append('/opt/Palm/za-bom/bin')
import ZAbom

@contextlib.contextmanager
def ContextLog(logger, oline, cline):
    """
    ContextLog(logger, oline, cline)

    Tell'em what you're gonna do, do something, then tell'em that you
    done it.
    """
    logger('{}...'.format(oline))
    yield
    logger('{}.'.format(cline))

class ZDGException(Exception):
    """
    Base class for all exceptions in this module.
    """
    pass

class ZDGComponentBlocked(ZDGException):
    """
    This exception is raised if a component has been specifically
    requested and yet that component is already locked.
    """
    pass

class SVNConnection(object):
    """
    Partial covering object for pysvn.
    """
    def __init__(self):
        self.connection = pysvn.Client()

        def get_log_message():
            return True, 'produced by rstool'

        self.connection.callback_get_log_message = get_log_message

    def co(self, here, there):
        try:
            self.connection.checkout(here, there)
        
        except pysvn.ClientError as err:
            self.trap(err)

    @staticmethod
    def trap(detail):
        if detail.args[0].find('callback_get_login required') >= 0:
            logger.critical('cannot access subversion - are you sure you are set up for password free access?')

        elif detail.args[0].find('PROPFIND request failed') >= 0:
            logger.critical('cannot access subversion - is there a problem reaching the server?')

        else:
            raise

    def revno(self, filename):
        return self.connection.info2(filename, recurse=False)[0][1].rev.number

class DependencyCheckerState(object):
    """
    An instance of this class represents the state of an entire post-commit checker.
    """

    def __init__(self, options, logger):
        self.options = options
        self.logger = logger
        self.locks = {}

    # file names and locations
    def attemptsdir(self):
        """
        Convenience accessor which refers to *options.attemptsdir*.
        """
        return self.options.attemptsdir

    def targetdir(self, component):
        """
        Convenience accessor for the name of the specific directory
        within *attemptsdir* for *component*.  (Currently
        *attemptsdir*/*component*)
        """
        return os.path.join(self.options.attemptsdir, component)

    # locking facilities
    def clear_locks(self):
        self.locks = {}

    def list_locks(self):
        return [lock for lock in self.locks]

    def test(self, name):
        """
        Attempt to lock *name* and return the result.
        """
        self.logger.debug('testing {}...'.format(name))

        try:
            result = True if self.locks[name] else False
            self.logger.debug('tested {} = {}.'.format(name, result))

        except KeyError:
            self.logger.debug('lock not (yet) listed {}.'.format(name))
            result = False

        return result

    def lock(self, pid, name):
        """
        Lock *name* for *pid*.
        """
        stealing = ''

        if name in self.locks:
            if self.locks[name] == pid:
                # already locked by this pid
                self.logger.debug('\'{}\' already locked by {}...'.format(name, pid))
                return True

            elif self.locks[name] in psutil.get_pid_list():
                # locked by another pid which is still live
                self.logger.debug('lock failed for \'{}\' held by {}...'.format(name, self.locks[name]))
                return False
            else:
                stealing = ' stealing'

        # at this point either the lock didn't exist or the locker is
        # no longer alive.  In either case, we can claim it.
        self.locks[name] = pid
        self.logger.debug('locked{} \'{}\' by {}...'.format(stealing, name, pid))
        return True

    def unlock(self, pid, name):
        """
        Attempt to unlock this component and return the result.
        """
        try:
            if self.locks[name] != pid:
                self.logger.debug('LockViolation \'{}\' by {}...'.format(name, pid))
                return False

            del self.locks[name]
            self.logger.debug('unlocked \'{}\' by {}'.format(name, pid))
            return True

        except KeyError:
            self.logger.debug('wasn\'t locked \'{}\' by {}'.format(name, pid))
            return True

    @staticmethod
    def ccapname(name):
        return 'component:' + name

    def lock_component(self, pid, name):
        return self.lock(pid, self.ccapname(name))

    def unlock_component(self, pid, name):
        return self.unlock(pid, self.ccapname(name))

    def components_by_stamp(self, stamp):
        """
        Iterator which returns a list of components in time stamp order.
        """
        for c in sorted(glob.glob(os.path.join(self.options.attemptsdir, '*', stamp)),
                          key=lambda f: os.stat(f).st_mtime):
            yield os.path.basename(os.path.dirname(c))

    def svn(self):
        if not hasattr(self, '_svn'):
            self._svn = SVNConnection()

        return self._svn

    def svnrev(self, filename):
        return self.svn().revno(filename)

    def oedir(self):
        """
        Lazy accessor which returns the name of a working directory
        checked out from subversion.  Will cleanup and check out the
        directory on the first access.
        """
        # if we've never read, (check out), the working dir, or if the
        # last time we did doesn't match what's available in the
        # repository...
        upstreamrev = self.svnrev(self.options.svnloc)
        if (not hasattr(self, '_last_read_oedir')
            or (self._last_read_oedir != upstreamrev)):

            self._oedir = self.options.oedir
            self.logger.debug('(Re)reading oedir: {}'.format(upstreamrev))

            if os.path.isdir(self._oedir):
                self.logger.debug('+ svn cleanup {}'.format(self._oedir))
                self.svn().connection.cleanup(self._oedir)

            self.logger.debug('+ svn co {} {}'.format(self.options.svnloc, self._oedir))
            self.svn().co(self.options.svnloc, self._oedir)
            downstreamrev = self.svnrev(self._oedir)
            self.logger.debug('Read oedir: {}'.format(downstreamrev))
            self._last_read_oedir = downstreamrev

        return self._oedir

    def _bbcomponentwalk(self):
        """
        Iterator which walks the *oedir* and lists all components found.
        """
        for path, subdirs, files in os.walk(self.oedir()):
            try:
                del subdirs[subdirs.index('.svn')]

            except ValueError:
                pass
                
            for file in files:
                pf, ext = os.path.splitext(file)
                if ext == '.bb':
                    yield pf.partition('_')[0]

    def components_by_bb(self):
        """
        Lazy accessor which returns a frozenset of components found by
        scanning *oedir* for bb files.
        """
        if (not hasattr(self, '_last_read_bb')
            or (self._last_read_bb != self._last_read_oedir)):

            self.logger.debug('(Re)reading bb files from {}...'.format(self.oedir()))
            self._components_by_bb = frozenset([b for b in self._bbcomponentwalk()])
            self._last_read_bb = self._last_read_oedir

        return self._components_by_bb

    def bomfile(self):
        if not hasattr(self, '_bomfile'):
            self._bomfile = self.options.bomfile or os.path.join(self.options.oedir, 'palm', 'conf', 'distro', 'nova-bom.inc')

        return self._bomfile


    def bom_obsolete(self, svnrevbom):
        return (not hasattr(self, '_last_read_bom')
                or (self._last_read_bom != svnrevbom))

    def bom(self):
        """
        Convenience accessor returning a :py:class:`ZAbom.bom` for the bom in *oedir*.
        """
        svnrevbom = self.svnrev(self.bomfile())

        if self.bom_obsolete(svnrevbom):
            self.logger.debug('(Re)reading bom from {}...'.format(self.bomfile()))
            self._bom = ZAbom.bom(self.bomfile())
            self._last_read_bom = svnrevbom

        return self._bom

    def components_by_bom(self):
        """
        Returns a frozenset of components found by reading our *bom*.
        """
        svnrevbom = self.svnrev(self.bomfile())

        if (not hasattr(self, '_last_read_by_bom')
            or (self._last_read_by_bom != self._last_read_bom)
            or (self.bom_obsolete(svnrevbom))):
           
            self.logger.debug('(Re)reading components from bom...')
            with ContextLog(self.logger.debug,
                            'Reading bom',
                            'Read'):
                self._components_by_bom = frozenset(self.bom().content.keys())

            self._last_read_by_bom = self._last_read_bom

        return self._components_by_bom

    def components_by_attempts(self):
        """
        Returns a frozenset of components found by scanning *attemptsdir*.
        """
        modtime = os.stat(self.options.attemptsdir).st_mtime if os.path.isdir(self.options.attemptsdir) else 0

        if (not hasattr(self, '_last_by_attempts')
            or (self._last_by_attempts != modtime)):

            self.logger.debug('(Re)reading attempts {}...'.format(time.asctime(time.localtime(modtime))))
            self._components_by_attempts = (frozenset([dir for dir in os.listdir(self.options.attemptsdir)])
                                            if os.path.isdir(self.options.attemptsdir)
                                            else frozenset([]))

            self._last_by_attempts = modtime

        return self._components_by_attempts

    def next(self, pid, requested_components):
        """
        An iterator which returns an ordered list of components to be
        tested.  *Requested_components* is a list of components which
        have been specifically requested.
        """
        requested_components = set(requested_components)
        real_components = self.components_by_bb() & self.components_by_bom()
        done = set([])

        # removals
        removals = self.components_by_attempts() - real_components
        self.logger.debug('{} removals'.format(len(removals), ' '.join(removals)))
        for component in removals:
            self.logger.info('removal: {}'.format(component))
            self.remove(pid, component)

        self._components_by_attempts &= real_components

        # requests - in request order
        self.logger.debug('{} requested components'.format(len(requested_components), ' '.join(requested_components)))
        for component in requested_components:
            if self.lock_component(pid, component):
                self.update(component)
                yield component
                done.add(component)
            else:
                self.logger.warning('component {} is blocked'.format(component))
                raise ZDGComponentBlocked

        # bumps - in stamp order
        bumps = list(self.components_by_stamp('bumped'))
        self.logger.debug('{} bumps: {}'.format(len(bumps), ' '.join(bumps)))
        for component in bumps:
            if (component not in done
                and self.lock_component(pid, component)):
                self.update(component)
                yield component
                done.add(component)

        # adds
        adds = real_components - self.components_by_attempts()
        self.logger.debug('{} adds: {}'.format(len(adds), (' '.join(adds
                                                                    if len(adds) < 10
                                                                    else list(adds)[0:10] + ['...']))))
        for component in sorted(adds):
            self.logger.info('addition: {}'.format(component))
            self.add(component)
            if self.lock_component(pid, component):
                yield component
                done.add(component)

        # regular
        regulars = list(self.components_by_stamp('status'))
        self.logger.debug('{} regulars: {}'.format(len(regulars), ' '.join(regulars)))
        for component in regulars:
            if (component not in done
                and self.lock_component(pid, component)):
                self.update(component)
                yield component
                done.add(component)

    def attemptdir(self, name):
        return os.path.join(self.options.attemptsdir, name)

    def update(self, name):
        """
        Update the attemptdir for *name* with current values.
        """
        attemptdir = self.attemptdir(name)

        try:
            os.makedirs(attemptdir)

        except OSError as err:
            self.logger.info('Could not mkdir {} (ignoring): {}'.format(attemptdir, err))
            pass

        with open(os.path.join(attemptdir, 'image'), 'w+') as f:
            try:
                f.write(self.bom().content[name].image)

            except KeyError:
                self.logger.error('ERROR: component {} is not in the bom'.format(name))
                raise ZDGComponentBlocked(name)

        with open(os.path.join(attemptdir, 'owner'), 'w+') as f:
            f.write(self.bom().content[name].owner)

        with open(os.path.join(attemptdir, 'version'), 'w+') as f:
            f.write(self.bom().content[name].version)

        with open(os.path.join(attemptdir, 'submission'), 'w+') as f:
            f.write(self.bom().content[name].submission)

    def add(self, name):
        """
        Create a new attemptdir for *name*, flagging it as new.
        """
        self.update(name)

        with open(os.path.join(self.attemptdir(name), 'new'), 'w+') as f:
            pass

    def remove(self, pid, name):
        """
        Remove the attemptdir for *component*.
        """
        with ContextLog(self.logger.debug,
                        'Removing {0}'.format(name),
                        'Removed {0}'.format(name)):

            self.lock_component(pid, name)
            topdir = os.path.join(self.options.attemptsdir, name)
            for path, subdirs, files in os.walk(topdir, topdown=False):
                for file in files:
                    thingy = os.path.join(path, file)

                    try:
                        self.logger.debug('Remove {}'.format(thingy))
                        os.remove(thingy)

                    except OSError:
                        self.logger.info('Could not rmdir {} (ignoring): {}'.format(thingy, os.strerror(err)))
                        pass

                for subdir in subdirs:
                    thingy = os.path.join(path, subdir)

                    try:
                        if os.path.islink(thingy):
                            self.logger.debug('Remove {} (link)'.format(thingy))
                            os.remove(thingy)
                        else:
                            self.logger.debug('Rmdir {}'.format(thingy))
                            os.rmdir(thingy)

                    except OSError:
                        self.logger.info('Could not rmdir {} (ignoring): {}'.format(thingy, os.strerror(err)))
                        pass

            self.logger.debug('Rmdir {}'.format(topdir))
            os.rmdir(topdir)
            self.unlock_component(pid, name)

class Handler(socketserver.StreamRequestHandler):
    greeting = 'ZApostd ready.\n'

    def respond(self, response):
        self.server.state.logger.debug('returning: {}'.format(response))
        self.wfile.write('{}\n'.format(response).encode('utf-8'))
        return

    def handle(self):
        self.server.state.logger.debug(self.greeting)
        self.wfile.write(self.greeting.encode('utf-8'))

        while True:
            self.server.state.logger.debug('looking for input...')
            cmd = self.rfile.readline().strip().decode('utf-8')

            if not len(cmd):
                return

            self.server.state.logger.debug('Received: {}'.format(cmd))

            cmd_split = collections.deque(cmd.split())

            todo = cmd_split.popleft()

            if todo == 'shutdown':
                self.server.state.logger.debug('shutting down...')
                #self.server.shutdown() # doesnt' seem to work single threaded
                self.server.socket.close()

                if self.server.address_family == socket.AF_UNIX:
                    os.remove(self.server.socketname)

                os._exit(0)

            if todo == 'locks':
                self.respond('locks ' + ' '.join(self.server.state.list_locks()))
                continue

            if todo == 'clear_locks':
                self.server.state.clear_locks()
                self.respond('clear_locks')
                continue

            if todo == 'test':
                lock = cmd_split.popleft()
                result = self.server.state.test(lock)
                self.respond('{} {} {}'.format(todo, lock, result))
                continue

            if todo in ['lock', 'unlock', 'next']:
                pid = int(cmd_split.popleft())

                if todo == 'next':
                    count = int(cmd_split.popleft())
                    result = self.server.state.next(pid, list(cmd_split))
                    self.respond('{} {} {} {}'.format(todo, pid, count, ' '.join(list(itertools.islice(result, count)))))
                    continue

                lock = cmd_split.popleft()

                if todo == 'lock':
                    result = self.server.state.lock(pid, lock)
                    self.respond('{} {} {} {}'.format(todo, pid, lock, result))
                    continue

                elif todo == 'unlock':
                    result = self.server.state.unlock(pid, lock)
                    self.respond('{} {} {} {}'.format(todo, pid, lock, result))
                    continue

            self.server.state.logger.debug('Unrecognized command: {}'.format(cmd))
            os._exit(22)

def getopts():
    u = ''
    u += 'usage: %prog\n'

    configs = configparser.ConfigParser()
    configs.read('/etc/za.conf')

    parser = optparse.OptionParser(usage = u)

    # General options
    general = optparse.OptionGroup(parser, 'General Options', '')

    general.add_option('-A', '--address', dest='address',
                       action='store', type='string', default='',
                       help='internet address on which to listen for connections.  (default: none)')

    general.add_option('-a', '--attemptsdir', dest='attemptsdir',
                       action='store', type='string', default='',
                       help='operate with the specific attemptsdir.  (default: ~/workdir/attempts)')

    general.add_option('-b', '--bomfile', dest='bomfile',
                       action='store', type='string', default='',
                       help='bom.  (default: ~/workdir/oe/palm/conf/distro/nova-bom.inc)')

    general.add_option('-e', '--oedir', dest='oedir',
                       action='store', type='string', default='',
                       help='directory to use for oe checkout.  (default: ~/workdir/oe)')

    general.add_option('-H', '--homedir', dest='homedir',
                       action='store', type='string', default='',
                       help='operate with the specific home directory.  (default: ~)')

    general.add_option('-l', '--logname', dest='logname',
                       action='store', type='string', default=os.getenv('LOGNAME', 'za-post'),
                       help='operate with the specific logname.  (default: LOGNAME from environment)')

    general.add_option('-n', '--now', dest='now',
                       action='store', type='int', default=0,
                       help='generate THIS many nexts immediately, then exit.  (default: 0)')

    general.add_option('-P', '--port', dest='port',
                       action='store', type='int', default='1962',
                       help='service port for internet connections.  (default: 1962)')

    general.add_option('-s', '--svnloc', dest='svnloc',
                       action='store', type='string', default=configs.get('za-post', 'svnloc'),
                       help='svn location.  (default: "{}")'.format(configs.get('za-post', 'svnloc')))

    general.add_option('-X', '--unixdomainsocket', dest='unixdomainsocket',
                       action='store', type='string', default='',
                       help='Use the specified unix domain socket.  (default: ~/workdir/zadc-socket)')

    general.add_option('-w', '--workdir', dest='workdir',
                       action='store', type='string', default=configs.get('za-post', 'workdir'),
                       help='operate with the specific workdir.  (default: {})'.format(configs.get('za-post', 'workdir')))

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

    if not options.logname:
        options.logname = os.getenv('LOGNAME', 'za-post')

    if not options.homedir:
        options.homedir = os.path.expanduser('~{}'.format(options.logname))

    if not options.workdir:
        options.workdir = os.path.join(options.homedir, 'workdir')

    if not options.oedir:
        options.oedir = os.path.join(options.workdir, 'oe')

    if not options.unixdomainsocket:
        options.unixdomainsocket = os.path.join(options.workdir, 'zadc-socket')

    if not options.attemptsdir:
        options.attemptsdir = os.path.join(options.workdir, 'attempts')

    if not options.svnloc:
        try:
            os.makedirs(options.workdir)

        except OSError as err:
            #logger.info('Could not mkdir {} (ignoring): {}'.format(attemptdir, os.strerror(err)))
            pass

    return options, args


def setupLogs(options):
    logger = logging.getLogger()

    if options.trace or options.logfile:
        loglevel = getattr(logging, options.loglevel.upper())

        f = logging.Formatter('%(asctime)s %(filename)s %(levelname)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')

        logger.setLevel(loglevel)

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

    logger.debug('workdir = {}'.format(options.workdir))
    logger.debug('oedir = {}'.format(options.oedir))
    logger.debug('svnloc = {}'.format(options.svnloc))
    logger.debug('attemptsdir = {}'.format(options.attemptsdir))
    logger.debug('uid = {} = {}'.format(os.getuid(), pwd.getpwuid(os.getuid()).pw_name))
    logger.debug('euid = {} = {}'.format(os.geteuid(), pwd.getpwuid(os.geteuid()).pw_name))
    logger.debug('gid = {} = {}'.format(os.getgid(), grp.getgrgid(os.getgid()).gr_name))
    logger.debug('egid = {} = {}'.format(os.getegid(), grp.getgrgid(os.getegid()).gr_name))

    return logger

if __name__ == '__main__':
    progname = sys.argv[0]

    options, args = getopts()

    logger = setupLogs(options)

    if options.now:
        state = DependencyCheckerState(options, logger)
        for i, n in zip(range(options.now), state.next(os.getpid(), args)):
            print(n)

        sys.exit(0)

    if options.address:
        who = socketserver.TCPServer
        where = (options.address, options.port)
        callit = '{}:{}'.format(options.address, options.port)
    else:
        who = socketserver.UnixStreamServer
        where = options.unixdomainsocket
        callit = where

    with ContextLog(logger.debug,
                    'Serving on {}...'.format(callit),
                    'Served.'):
        server=who(where, Handler)
        server.socketname = options.unixdomainsocket
        server.state = DependencyCheckerState(options, logger)
        server.serve_forever()

    sys.exit(retval)

# eof
