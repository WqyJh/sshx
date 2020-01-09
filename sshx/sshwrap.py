import sys
import time
import struct
import termios
import signal
import fcntl
import threading
import subprocess
import paramiko


from . import const as c
from . import utils, logger, cfg
from .sshx_forward import Forwards
from .const import STATUS_SUCCESS, STATUS_FAIL


LOCALHOST = '127.0.0.1'

ServerAliveInterval = 0
ServerAliveCountMax = 3


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
{extras} {forwards} {jump} -p {port} {user}@{host} {exec}'
_SSH_COMMAND_IDENTITY = 'ssh -i {identity} {extras} {forwards} {jump} -p {port} {user}@{host} {exec}'
_SSH_DEST = '{user}@{host}:{port}'
_SCP_COMMAND_PASSWORD = 'scp -r \
-oPreferredAuthentications=password \
-oStrictHostKeyChecking=no \
-oUserKnownHostsFile=/dev/null \
{jump} -P {port} {src} {dst}'
_SCP_COMMAND_IDENTITY = 'scp -r -i {identity} {jump} -P {port} {src} {dst}'


def find_vias(vias):
    '''Find accounts by vias.'''
    _vias = vias.split(',')
    return [cfg.config.get_account(v, decrypt=True) for v in _vias]


def find_jumps(account):
    '''Find accounts by account.via.'''
    jumps = []
    a = cfg.config.get_account(account.via, decrypt=True)
    while a:
        jumps.append(a)
        a = cfg.config.get_account(a.via, decrypt=True)
    return jumps


def compile_jumps(account, vias=None, prefix='-J '):
    jumps = find_vias(vias) if vias else find_jumps(account)

    if jumps:
        accounts = list(jumps)
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
    # : interact=True background=False
    # -f: interact=True background=True
    # -fNT: interact=False background=True
    # -NT: interact=False background=False
    if interact:
        if background:
            extras += ' -f'
    else:
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
        command = _SSH_COMMAND_IDENTITY.format(
            jump=jump,
            forwards=_forwards,
            user=account.user,
            host=account.host,
            port=account.port,
            identity=account.identity,
            extras=extras,
            exec=exec)
    else:
        command = _SSH_COMMAND_PASSWORD.format(
            jump=jump,
            forwards=_forwards,
            user=account.user,
            host=account.host,
            port=account.port,
            extras=extras,
            exec=exec)
    command = utils.format_command(command)

    # connect
    p = None
    try:
        logger.debug(command)

        p = pexpect.spawn(command)

        # Passwords for jump hosts
        if passwords:
            for password in passwords:
                r = p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
                if r == 0:
                    logger.error(c.MSG_CONNECTION_TIMED_OUT)
                    return STATUS_FAIL
                p.sendline(password)

        # Password for dest host
        if not account.identity:
            r = p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
            if r == 0:
                logger.error(c.MSG_CONNECTION_TIMED_OUT)
                return STATUS_FAIL
            p.sendline(account.password)

        if background:
            p.interact(escape_character=None)
        else:
            set_winsize(p)  # Adjust window size
            # Set auto-adjust window size
            signal.signal(signal.SIGWINCH, sigwinch_passthrough(p))
            r = p.expect([pexpect.TIMEOUT, '\S'])
            if r == 0:
                logger.error(c.MSG_CONNECTION_TIMED_OUT)
                return STATUS_FAIL
            p.write_to_stdout(p.after)
            p.interact(escape_character=None)
        logger.debug(f'exit status code: {p.status}')
        return STATUS_SUCCESS
    except Exception as e:
        logger.error(c.MSG_CONNECTION_ERROR)
        logger.debug(e)
        return STATUS_FAIL


def scp_pexpect(account, targets, vias):
    import pexpect

    jump, passwords = compile_jumps(account, vias=vias, prefix='-oProxyJump=')

    src, dst = targets.src.compile(), targets.dst.compile()

    if account.identity:
        command = _SCP_COMMAND_IDENTITY.format(
            jump=jump,
            port=account.port,
            src=src,
            dst=dst,
            identity=account.identity)
    else:
        command = _SCP_COMMAND_PASSWORD.format(
            jump=jump,
            port=account.port,
            src=src,
            dst=dst)
    command = utils.format_command(command)

    p = None
    try:
        logger.debug(command)

        p = pexpect.spawn(command)

        # Passwords for jump hosts
        if passwords:
            for password in passwords:
                r = p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
                if r == 0:
                    logger.error(c.MSG_CONNECTION_TIMED_OUT)
                    return STATUS_FAIL
                p.sendline(password)

        # Password for dest host
        if not account.identity:
            r = p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
            if r == 0:
                logger.error(c.MSG_CONNECTION_TIMED_OUT)
                return STATUS_FAIL
            p.sendline(account.password)

        set_winsize(p)  # Adjust window size
        # Set auto-adjust window size
        signal.signal(signal.SIGWINCH, sigwinch_passthrough(p))

        r = p.expect([pexpect.TIMEOUT, '\S'])
        if r == 0:
            logger.error(c.MSG_CONNECTION_TIMED_OUT)
            return STATUS_FAIL

        p.write_to_stdout(p.after)
        p.interact()
        return STATUS_SUCCESS
    except Exception as e:
        logger.error(c.MSG_CONNECTION_ERROR)
        logger.debug(e)
        return STATUS_FAIL


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


def scp_pexpect2(account, targets, vias):
    import pexpect

    jumps = find_vias(vias) if vias else find_jumps(account)

    port = account.port
    host = account.host

    if jumps:
        jump1 = jumps.pop()
        host = LOCALHOST
        port = find_available_port()
        maps = '%s:%s:%s:%s' % (host, port, account.host, account.port)
        forwards = Forwards(maps, '')

        # Establish port forwarding
        vias = ','.join([a.name for a in jumps])
        ret = ssh_pexpect2(jump1, vias=vias, forwards=forwards,
                           interact=False, background=True)
        if ret == STATUS_FAIL:
            return STATUS_FAIL

    src, dst = targets.src.compile(host=host), \
        targets.dst.compile(host=host)

    if account.identity:
        command = _SCP_COMMAND_IDENTITY.format(
            jump='',
            port=port,
            src=src,
            dst=dst,
            identity=account.identity)
    else:
        command = _SCP_COMMAND_PASSWORD.format(
            jump='',
            port=port,
            src=src,
            dst=dst)
    command = utils.format_command(command)

    p = None
    try:
        logger.debug(command)

        p = pexpect.spawn(command)

        # Password for dest host
        if not account.identity:
            r = p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
            if r == 0:
                logger.error(c.MSG_CONNECTION_TIMED_OUT)
                return STATUS_FAIL
            p.sendline(account.password)

        set_winsize(p)  # Adjust window size
        # Set auto-adjust window size
        signal.signal(signal.SIGWINCH, sigwinch_passthrough(p))

        r = p.expect([pexpect.TIMEOUT, '\S'])
        if r == 0:
            logger.error(c.MSG_CONNECTION_TIMED_OUT)
            return STATUS_FAIL

        p.write_to_stdout(p.after)
        p.interact()
        return STATUS_SUCCESS
    except Exception as e:
        logger.error(c.MSG_CONNECTION_ERROR)
        logger.debug(e)
        return STATUS_FAIL


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


def scp(account, targets, vias=None, with_forward=False):
    if with_forward:
        return scp_pexpect2(account, targets, vias)
    return scp_pexpect(account, targets, vias)
