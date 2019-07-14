# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

import socket
import os
import sys
from paramiko.py3compat import u

# windows does not have termios...
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    import colorama

    has_termios = False

from . import utils

ENTER = 0x0D


def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        colorama.init()
        windows_shell(chan)
        colorama.deinit()

        import win32api
        win32api.keybd_event(ENTER, 0, 0, 0)


def posix_shell(chan):
    import select

    oldtty = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        while True:
            r, w, e = select.select([chan, sys.stdin], [], [])
            if chan in r:
                try:
                    x = chan.recv(1024)
                    if len(x) == 0:
                        #sys.stdout.write("\r\n*** EOF\r\n")
                        break
                    
                    sys.stdout.write(x.decode('utf-8'))
                    sys.stdout.flush()
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = sys.stdin.read(1)
                if len(x) == 0:
                    break
                chan.send(x)
        
                # There will be a '\x1b[44;17R' before every new line.
                # I don't know what it is. Just throw it.
                if x == '\x1b':
                    x = sys.stdin.read(7)
                    #print(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write(
        "Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n"
    )

    def sending(sock):
        try:
            while True:
                d = utils.getch()
                if not d:
                    break

                chan.send(d)
        except socket.error:
            # connection closed
            pass

    def receiving(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.flush()
                break

            # 2018/06/05
            # Crash when receiving b'\xe0', but it can't solve easily.
            # When pressing direction key UP, a b'\xe0H' sequence will
            # be read through getch() method, and will be send to the 
            # server. However, server can't recognize b'\xe0', so it 
            # will be echoed onto the screen, therefore, it shows in
            # the received data and cause a decoding fail.
            # To solve the problem, we can't press the special key like
            # direction key, page up and down.
            # Another solution is, parsing the special key to ANSI escape
            # sequence, I'v succeed in parsing direction keys, PgUp and PgDn. 
            # I viewed the openssh client source code ported by microsoft 
            # (https://github.com/PowerShell/openssh-portable).
            # Then I don't think it's easy.
            # So I decide to implement interactive shell on paramiko
            # for windows later, and using os.system("ssh") for instead.
            sys.stdout.write(data.decode())
            
            # can't write bytes directly, cause it won't
            # escape the ANSI escape sequence
            # sys.write(sys.stdout.fileno(), data)

            sys.stdout.flush()

    worker = threading.Thread(target=sending, args=(chan,))
    worker.start()

    receiving(chan)
