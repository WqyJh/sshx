from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import sys
import time
import struct
import termios
import signal
import fcntl
import threading
import subprocess
import paramiko

from .interactive import interactive_shell

from . import utils
from .cfg import read_account
from .sshx_forward import Forwards

if not utils.PY3:
    FileNotFoundError = IOError

if utils.NT:
    from pykeyboard import PyKeyboard


LOCALHOST = '127.0.0.1'


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


def ssh_paramiko(account):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if account.identity:
        def f(): return client.connect(account.host, int(account.port),
                                       account.user, key_filename=account.identity)
        use_password = False
    else:
        def f(): return client.connect(account.host, int(account.port),
                                       account.user, password=account.password)
        use_password = True
    msg = _connect(f, use_password)

    if msg['status'] == 'success':
        chan = client.invoke_shell()
        interactive_shell(chan)
        return {
            'status': 'success',
            'msg': 'Connection to %s closed.' % account.host,
        }
    else:
        return msg


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


def ssh_pexpect(account):
    from pexpect import pxssh
    s = pxssh.pxssh(options=dict(StrictHostKeyChecking="no",
                                 UserKnownHostsFile="/dev/null"))

    if account.identity:
        s.login(account.host, account.user, port=account.port,
                ssh_key=account.identity, auto_prompt_reset=False)
    else:
        s.login(account.host, account.user, port=account.port,
                password=account.password, auto_prompt_reset=False)

    set_winsize(s)  # Adjust window size
    # Set auto-adjust window size
    signal.signal(signal.SIGWINCH, sigwinch_passthrough(s))

    # If don't send an '\n', users have to press enter manually after
    # interact() is called
    s.send('\x1b\x00')  # Send Esc
    s.interact()


_SSH_COMMAND_PASSWORD = 'ssh {jump} {forwards} {user}@{host} -p {port} \
-o PreferredAuthentications=password \
-o StrictHostKeyChecking=no \
-o UserKnownHostsFile=/dev/null'
_SSH_COMMAND_IDENTITY = 'ssh {jump} {forwards} {user}@{host} -p {port} -i {identity}'
_SSH_DEST = '{user}@{host}:{port}'
_SCP_COMMAND_PASSWORD = 'scp -r \
-oPreferredAuthentications=password \
-oStrictHostKeyChecking=no \
-oUserKnownHostsFile=/dev/null \
-P {port} {jump} {src} {dst}'
_SCP_COMMAND_IDENTITY = 'scp -r -P {port} {jump} {src} {dst} -i {identity}'


def find_vias(vias):
    _vias = vias.split(',')
    return [read_account(v) for v in reversed(_vias)]


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


def ssh_pexpect2(account, vias=None, forwards=None):
    import pexpect
    jump, passwords = compile_jumps(account, vias=vias)

    _forwards = forwards.compile() if forwards else ''

    if account.identity:
        command = _SSH_COMMAND_IDENTITY.format(jump=jump,
                                               forwards=_forwards,
                                               user=account.user,
                                               host=account.host,
                                               port=account.port, identity=account.identity)
    else:
        command = _SSH_COMMAND_PASSWORD.format(jump=jump,
                                               forwards=_forwards,
                                               user=account.user,
                                               host=account.host,
                                               port=account.port)
    try:
        print(command)

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

        # If don't send an '\n', users have to press enter manually after
        # interact() is called
        # p.send('\x1b\x00')  # Send Esc
        p.interact()
    except Exception as e:
        return {
            'status': 'success',
            'msg': 'Connection failed',
        }


def ssh_pexpect3(account, vias=None, forwards=None):
    import pexpect
    jump, passwords = compile_jumps(account, vias=vias)

    _forwards = forwards.compile(prefix='') if forwards else ''

    if account.identity:
        command = _SSH_COMMAND_IDENTITY.format(jump=jump,
                                               forwards=_forwards,
                                               user=account.user,
                                               host=account.host,
                                               port=account.port, identity=account.identity)
    else:
        command = _SSH_COMMAND_PASSWORD.format(jump=jump,
                                               forwards=_forwards,
                                               user=account.user,
                                               host=account.host,
                                               port=account.port)
    try:
        print(command)

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

        p.send('\x1b\x00')  # Send Esc
        p.sendline()

        return {
            'status': 'success',
            'msg': 'Connected',
            'p': p,
        }
    except Exception as e:
        return {
            'status': 'fail',
            'msg': 'Connection failed %s' % e,
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
        print(command)

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
        return {
            'status': 'success',
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
    import re
    import pexpect

    jump1 = jumps.pop(0)
    port = find_available_port()
    maps = '%s:%s:%s:%s' % (LOCALHOST, port, account.host, account.port)
    forwards = Forwards(maps, '')

    print(maps)

    # Establish port forwarding
    vias = ','.join([a.name for a in reversed(jumps)])
    ret = ssh_pexpect3(jump1, vias=vias, forwards=forwards)
    if ret['status'] == 'fail':
        return ret

    forwarding = ret['p']

    print(targets)

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
        print(command)

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
        return {
            'status': 'success',
            'msg': 'Connection failed: %s' % e,
        }


def _ssh_command_password(account):
    def input_password(password):
        # delay 1s
        time.sleep(1)
        # input password
        k = PyKeyboard()
        k.type_string(password)
        k.tap_key(k.enter_key)

    threading.Thread(target=input_password, args=(account.password,)).start()
    try:
        command = _SSH_COMMAND_PASSWORD.format(
            host=account.host, port=account.port, user=account.user).split()
        return subprocess.call(command)
    except Exception:
        sys.stdin.flush()


def ssh_command(account, vias=None, forwards=None):
    if utils.NT:
        if account.identity:
            command = _SSH_COMMAND_IDENTITY.format(
                host=account.host, port=account.port,
                user=account.user, identity=account.identity).split()
            return subprocess.call(command)
        else:
            _ssh_command_password(account)
    else:
        # ssh_pexpect(account)
        ssh_pexpect2(account, vias=vias, forwards=forwards)


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


def ssh(account, vias=None, forwards=None):
    if has_command('ssh'):
        return ssh_command(account, vias=vias, forwards=forwards)
    else:
        return ssh_paramiko(account)


def scp(account, targets, vias=None):
    jumps = find_vias(vias) if vias else find_jumps(account)

    if jumps:
        return scp_pexpect2(account, targets, jumps)
    return scp_pexpect(account, targets)
