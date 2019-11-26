import sys
import time
import struct
import termios
import signal
import fcntl
import threading
import subprocess
import paramiko

from sshx import logger

from . import utils
from .cfg import read_account
from .sshx_forward import Forwards


LOCALHOST = '127.0.0.1'

ServerAliveInterval = 0
ServerAliveCountMax = 3


def _connect(f, use_password):
    exception = None

    try:
        f()
    except Exception as e:
        exception = e

    if exception is None:
        return {
            'status': 'success',
        }

    if isinstance(exception, paramiko.AuthenticationException):
        return {
            'status': 'fail',
            'msg': 'Authentication failed, invalid %s!' % 'password' if use_password else 'identity file',
        }
    else:
        return {
            'status': 'fail',
            'msg': 'Connection Error',
        }


def set_winsize(p):
    s = struct.pack("HHHH", 0, 0, 0, 0)
    a = struct.unpack('hhhh', fcntl.ioctl(
        sys.stdout.fileno(), termios.TIOCGWINSZ, s))

    if not p.closed:
        p.setwinsize(a[0], a[1])


def sigwinch_passthrough(p):
    def _sigwinch_passthrough(sig, data):
        '''
        Adjust the window size automatically when the window size changed.

        Reference: https://pexpect.readthedocs.io/en/stable/api/pexpect.html?highlight=interactive#pexpect.spawn.interact.
        '''
        set_winsize(p)

    return _sigwinch_passthrough


_SSH_COMMAND_PASSWORD = 'ssh \
-o PreferredAuthentications=password \
-o StrictHostKeyChecking=no \
-o UserKnownHostsFile=/dev/null \
{extras} {jump} {forwards} {user}@{host} -p {port} {exec}'
_SSH_COMMAND_IDENTITY = 'ssh {extras} {jump} {forwards} {user}@{host} -p {port} -i {identity} {exec}'
_SSH_DEST = '{user}@{host}:{port}'
_SCP_COMMAND_PASSWORD = 'scp -r \
-oPreferredAuthentications=password \
-oStrictHostKeyChecking=no \
-oUserKnownHostsFile=/dev/null \
-P {port} {jump} {src} {dst}'
_SCP_COMMAND_IDENTITY = 'scp -r -P {port} {jump} {src} {dst} -i {identity}'


def find_vias(vias):
    _vias = vias.split(',')
    return [read_account(v) for v in _vias]


def find_jumps(account):
    jumps = []

    a = read_account(account.via)
    while a:
        jumps.append(a)
        a = read_account(a.via)
    return jumps


def compile_jumps(account, vias=None, prefix='-J '):
    jumps = find_vias(vias) if vias else find_jumps(account)

    if jumps:
        accounts = list(reversed(jumps))
        dests = [_SSH_DEST.format(
            user=a.user, host=a.host, port=a.port) for a in accounts]
        jump = prefix + ','.join(dests)
        passwords = [a.password for a in accounts]
    else:
        jump = ''
        passwords = []

    return jump, passwords


def ssh_pexpect2(account, vias=None, forwards=None, extras='', interact=True, background=False, exec=''):
    import pexpect
    jump, passwords = compile_jumps(account, vias=vias)

    # interactive/background/foreground config
    if not interact:
        '''
        -f              background
        -N              do not execute remote command
        -T              do not allocate pty
        -fNT            non interactive
        '''
        extras += (' -fNT' if background else ' -NT')

    # keep alive config
    if ServerAliveInterval > 0:
        extras += f' -o ServerAliveInterval={ServerAliveInterval} -o ServerAliveCountMax={ServerAliveCountMax}'

    # port forwarding config
    _forwards = forwards.compile() if forwards else ''

    # compile command
    if account.identity:
        command = _SSH_COMMAND_IDENTITY.format(jump=jump,
                                               forwards=_forwards,
                                               user=account.user,
                                               host=account.host,
                                               port=account.port, identity=account.identity,
                                               extras=extras,
                                               exec=exec)
    else:
        command = _SSH_COMMAND_PASSWORD.format(jump=jump,
                                               forwards=_forwards,
                                               user=account.user,
                                               host=account.host,
                                               port=account.port,
                                               extras=extras,
                                               exec=exec)

    # connect
    try:
        logger.debug(command)

        p = pexpect.spawn(command)

        # Passwords for jump hosts
        if passwords:
            for password in passwords:
                p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
                p.sendline(password)

        # Password for dest host
        if not account.identity:
            p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
            p.sendline(account.password)

        set_winsize(p)  # Adjust window size
        # Set auto-adjust window size
        signal.signal(signal.SIGWINCH, sigwinch_passthrough(p))

        p.interact()

    except Exception as e:
        logger.debug(e)
        return {
            'status': 'fail',
            'msg': 'Connection failed',
        }


def scp_pexpect(account, targets):
    import pexpect

    jump, passwords = compile_jumps(account, prefix='-oProxyJump=')

    src, dst = targets.src.compile(), targets.dst.compile()

    if account.identity:
        command = _SCP_COMMAND_IDENTITY.format(jump=jump,
                                               port=account.port,
                                               src=src,
                                               dst=dst,
                                               identity=account.identity)
    else:
        command = _SCP_COMMAND_PASSWORD.format(jump=jump,
                                               port=account.port,
                                               src=src,
                                               dst=dst)
    try:
        logger.debug(command)

        p = pexpect.spawn(command)

        # Passwords for jump hosts
        if passwords:
            for password in passwords:
                p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
                p.sendline(password)

        # Password for dest host
        if not account.identity:
            p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
            p.sendline(account.password)

        set_winsize(p)  # Adjust window size
        # Set auto-adjust window size
        signal.signal(signal.SIGWINCH, sigwinch_passthrough(p))

        p.interact()
    except Exception as e:
        logger.debug(e)
        return {
            'status': 'fail',
            'msg': 'Connection failed',
        }


def find_available_port():
    import socket
    import random

    while True:
        port = random.randint(50000, 60000)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex((LOCALHOST, port))
            if res == 0:
                continue
            return port


def scp_pexpect2(account, targets, jumps):
    import pexpect

    jump1 = jumps.pop(0)
    port = find_available_port()
    maps = '%s:%s:%s:%s' % (LOCALHOST, port, account.host, account.port)
    forwards = Forwards(maps, '')

    # Establish port forwarding
    vias = ','.join([a.name for a in reversed(jumps)])
    ret = ssh_pexpect2(jump1, vias=vias, forwards=forwards, interact=False)
    if ret['status'] == 'fail':
        return ret

    forwarding = ret['p']

    src, dst = targets.src.compile(host=LOCALHOST), \
        targets.dst.compile(host=LOCALHOST)

    if account.identity:
        command = _SCP_COMMAND_IDENTITY.format(jump='',
                                               port=port,
                                               src=src,
                                               dst=dst,
                                               identity=account.identity)
    else:
        command = _SCP_COMMAND_PASSWORD.format(jump='',
                                               port=port,
                                               src=src,
                                               dst=dst)
    try:
        logger.debug(command)

        p = pexpect.spawn(command)

        # Password for dest host
        if not account.identity:
            p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
            p.sendline(account.password)

        set_winsize(p)  # Adjust window size
        # Set auto-adjust window size
        signal.signal(signal.SIGWINCH, sigwinch_passthrough(p))

        p.interact()
    except Exception as e:
        logger.debug(e)
        return {
            'status': 'fail',
            'msg': 'Connection failed',
        }


def has_command(command):
    try:
        subprocess.check_call(command,
                              stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    except FileNotFoundError:
        return False
    except Exception:
        pass
    return True


def ssh(account, vias=None, forwards=None, extras='', interact=True, background=False, exec=''):
    return ssh_pexpect2(account, vias=vias, forwards=forwards, extras=extras,
                        interact=interact, background=background, exec=exec)


def scp(account, targets, vias=None):
    jumps = find_vias(vias) if vias else find_jumps(account)

    if jumps:
        return scp_pexpect2(account, targets, jumps)
    return scp_pexpect(account, targets)
