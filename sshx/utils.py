import os
import sys
import json
import string
import random

from getpass import getpass as _getpass

NT = os.name == 'nt'

if NT:
    from msvcrt import getch as _getch
    import win32api
    import win32con
else:
    #from getch import getch as _getch
    pass


class ClsDictEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


def random_str(length):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(15)])


def is_str(s):
    return isinstance(s, str)


def json_dump(obj):
    return json.dumps(obj, cls=ClsDictEncoder)


def json_load(s):
    return json.loads(s)


SPECIAL_KEY_MAP = {
    b'H': b'\x1b[A',  # Up
    b'P': b'\x1b[B',  # Down
    b'K': b'\x1b[D',  # Left
    b'M': b'\x1b[C',  # Right
    b'G': b'\x1b[H',  # Home
    b'O': b'\x1b[4~',  # End
    # b'I': b'\x1b[E', # PgUp
    # b'Q': b'\x1b[E', # PgDn
}


def getch():
    if NT:
        # Any visible key is fellowed by an b'\x00'
        c = _getch()
        if c == b'\x00':
            c = _getch()

        # Some of the special keys like direction key
        # and Home, PgDn start with an b'\xe0'.
        if c == b'\xe0':
            c = _getch()
            # print(c, SPECIAL_KEY_MAP.get(c, b''))
            c = SPECIAL_KEY_MAP.get(c, b'')

        return c
    else:
        c = getch()
    return c


def read_password():
    return _getpass()


def press_key(key):
    win32api.keybd_event(key, 0, win32con.KEYEVENT, 0)
