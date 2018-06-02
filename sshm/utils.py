from __future__ import unicode_literals

import os
import sys
import json
import string
import random

NT = os.name == 'nt'

PY3 = sys.version > '3'

if NT:
    from msvcrt import getch as _getch
else:
    #from getch import getch as _getch
    pass


def random_str(length):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(15)])


def is_str(s):
    if PY3:
        return isinstance(s, str)
    else:
        return isinstance(s, unicode)

def json_dump(obj):
    if PY3:
        return json.dumps(obj)
    else:
        return json.dumps(obj).decode('utf-8')

def json_load(s):
    if PY3:
        return json.loads(s)
    else:
        return json.loads(s.encode('utf-8'))


def getch():
    if NT:
        if PY3:
            c = _getch()
            _getch()
        else:
            c = _getch()
    else:
        c = getch()
    return c