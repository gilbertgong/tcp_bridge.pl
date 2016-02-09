#!/usr/bin/python

# Copyright (c) 2015, gilbertgong, johann8384
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of tcp_bridge.pl nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Listens on a local TCP socket for incoming Metrics """

"""This tcollector features a watchfile, if you run tail -f on this file,
you can monitor the metrics it is submitting"""

import socket
import os
import sys
import time
from thread import *

DEV_MODE = False
try:
    from collectors.lib import utils
except ImportError:
    print >> sys.stderr, 'unable to import utils from collectors.lib'
    DEV_MODE = True

try:
    from collectors.etc import tcp_bridge_conf
except ImportError:
    print >> sys.stderr, 'unable to import tcp_bridge_conf'
    tcp_bridge_conf = None

HOST = '127.0.0.1'
PORT = 4243
WATCHFILE = '/dev/shm/tcp_bridge.out'
WATCH_ENABLE = True

if DEV_MODE:
    print >> sys.stderr, 'running in DEV_MODE, using file defaults'

# metrics
m_namespace = 'tcollector.tcp_bridge.'
m_lines = 0
m_connections = 0
m_delay = 15
m_last = 0
m_ptime = 0

# buffered stdout seems to break metrics
out = os.fdopen(sys.stdout.fileno(), 'w', 0)
watch = None

def reset_watch():
    if not WATCH_ENABLE:
        return

    global watch
#    watch.truncate(0)
    watch.close()
    watch = open(WATCHFILE, 'w', 0)

def printm(string, time, value):
    out.write(m_namespace+string+' '+str(time)+' '+str(value)+'\n')
    if WATCH_ENABLE:
        watch.write(m_namespace+string+' '+str(time)+' '+str(value)+'\n')

def printmetrics():
    global m_delay
    global m_last

    ts = int(time.time())
    if ts > m_last+m_delay:
        printm('lines_read', ts, m_lines)
        printm('connections_processed', ts, m_connections)
        printm('processing_time', ts, m_ptime)
        printm('active', ts, 1)
        m_last = ts

def clientthread(connection):
    global m_lines
    global m_connections
    global m_ptime
    global watch

    reset_watch()
    start = time.time()
    f = connection.makefile()
    while True:
        data = f.readline()
        m_lines += 1

        if not data:
            break

        data = removePut(data)
        out.write(data)
        if WATCH_ENABLE:
            watch.write(data)

    f.close()
    connection.close()

    end = time.time()
    m_ptime += (end - start)
    m_connections += 1
    printmetrics()

def removePut(line):
    if line.startswith('put '):
        return line[4:]
    else:
        return line

def mydrop():
    if not DEV_MODE:
        utils.drop_privileges()
    elif os.getuid() == 0:
        print >> sys.stderr, 'do not run as root in DEV MODE, exiting'
        sys.exit(1)

def initialize():
    global HOST
    global PORT

    # if DEV_MODE use defaults
    if not DEV_MODE:
        
        if not (tcp_bridge_conf and tcp_bridge_conf.enabled()):
            print >> sys.stderr, 'not enabled, or tcp_bridge_conf unavilable'
            sys.exit(13)

        # override local vars if available
        if tcp_bridge_conf.port():
            PORT = tcp_bridge_conf.port()

        if tcp_bridge_conf.host():
            HOST = tcp_bridge_conf.host()

    mydrop()

    # open watch after drop privs
    global watch
    if WATCH_ENABLE:
        watch = open(WATCHFILE, 'w', 0)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((HOST, PORT))
        sock.listen(1)

    except socket.error, msg:
        print >> sys.stderr, 'could not open socket: %s' % msg
        sys.exit(1)

    return sock

def main():
    sock = initialize()

    try:
        try:
            while 1:
                connection, address = sock.accept()
                start_new_thread(clientthread, (connection,))

        except KeyboardInterrupt:
            print >> sys.stderr, "keyboard interrupt, exiting"

    finally:
        sock.close()

if __name__ == "__main__":
    main()

sys.exit(0)
