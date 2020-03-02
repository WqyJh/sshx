# -*- coding: future_fstrings -*-

import os
import json
import string
import random

from getpass import getpass

from . import const as c
from . import logger


class ClsDictEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


def random_str(length):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(15)])


def is_str(s):
    return isinstance(s, str)


def json_dump(obj):
    return json.dumps(obj, cls=ClsDictEncoder, indent=4)


def json_load(s):
    return json.loads(s)


def read_password(prompt='Password:'):
    '''Read password from PTY'''
    return getpass(prompt=prompt)


def read_passphrase():
    return read_password(prompt='Passphrase:')


def parse_user_host_port(s):
    '''
    user@host:port -> (user, host, port)
    '''
    user, host_port = s.split('@')
    splited = host_port.split(':')

    if len(splited) == 2:
        host, port = splited
    else:
        host, port = splited[0], c.DEFAULT_PORT

    return user, host, port


def format_command(s):
    '''Remove duplicate spaces in s and remove the leading and tailing spaces.'''
    return ' '.join(s.split())


def kill_by_command(command):
    import psutil

    for p in psutil.process_iter():
        if p.name() in command:
            if command in ' '.join(p.cmdline()):
                p.terminate()
                gone, alive = psutil.wait_procs([p], timeout=3)
                if p in alive:
                    p.kill()
                    logger.debug(f'process killed: {command}')
                else:
                    logger.debug(f'process terminated: {command}')


def sshkey_exists(identity):
    return os.path.isfile(identity)


def sshkey_has_passphrase(identity):
    with open(identity, 'r') as f:
        return 'Proc-Type: 4,ENCRYPTED' in f.read()


def sshkey_check_passphrase(identity, passphrase):
    if not sshkey_has_passphrase(identity):
        return passphrase == ''

    import pexpect
    cmd = f'env SSH_ASKPASS=/bin/false ssh-keygen -y -f {identity}'

    logger.debug(cmd)

    p = pexpect.spawn(cmd)
    r = p.expect([pexpect.EOF, 'passphrase:'])
    if r == 0:
        return False
    p.sendline(passphrase)
    p.wait()
    return p.status == 0
