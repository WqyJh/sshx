import sys
import time
import struct
import termios
import signal
import fcntl
import threading
import subprocess
import paramiko
import pexpect


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
-oExitOnForwardFailure=yes \
{extras} {forwards} {jump} -p {port} {user}@{host} {cmd}'
_SSH_COMMAND_IDENTITY = 'ssh -oExitOnForwardFailure=yes \
-i {identity} {extras} {forwards} {jump} -p {port} {user}@{host} {cmd}'
_SSH_DEST = '{user}@{host}:{port}'
_SCP_COMMAND_PASSWORD = 'scp -r \
-oPreferredAuthentications=password \
-oStrictHostKeyChecking=no \
-oUserKnownHostsFile=/dev/null \
-oExitOnForwardFailure=yes \
{jump} -P {port} {src} {dst}'
_SCP_COMMAND_IDENTITY = 'scp -oExitOnForwardFailure=yes \
-r -i {identity} {jump} -P {port} {src} {dst}'


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


class SSHPexpect(object):
    def __init__(self, account, vias=None, forwards=None, extras='', tty=True, background=False, execute=True, cmd='', detach=False):
        self.account = account
        self.vias = vias
        self.forwards = forwards
        self.extras = extras
        self.execute = execute
        self.cmd = cmd

        # detach    background  self.detach self.background
        # True      True        True        False
        # True      False       False       False
        # False     True        False       True
        # False     False       False       False
        self.detach = background and detach
        self.background = False if self.detach else background
        self.tty = False if self.detach else tty

        self.thread = None

        self.p = None

    def compile_flags(self):
        _flags_maps = [
            {True: '', False: 'N'},
            {True: '', False: 'T'},
        ]
        _flags = [self.execute, self.tty]
        flags = ''.join([m[f] for m, f in zip(_flags_maps, _flags)])
        return f' -{flags}' if flags else ''

    def compile_command(self):
        self.jump, self.passwords = compile_jumps(self.account, vias=self.vias)

        if not self.account.identity:
            self.passwords.append(self.account.password)

        self.extras += self.compile_flags()

        # keep alive config
        if ServerAliveInterval > 0:
            self.extras += f' -o ServerAliveInterval={ServerAliveInterval} -o ServerAliveCountMax={ServerAliveCountMax}'

        # port forwarding config
        _forwards = self.forwards.compile() if self.forwards else ''

        account = self.account
        if account.identity:
            command = _SSH_COMMAND_IDENTITY.format(
                jump=self.jump,
                forwards=_forwards,
                user=account.user,
                host=account.host,
                port=account.port,
                identity=account.identity,
                extras=self.extras,
                cmd=self.cmd)
        else:
            command = _SSH_COMMAND_PASSWORD.format(
                jump=self.jump,
                forwards=_forwards,
                user=account.user,
                host=account.host,
                port=account.port,
                extras=self.extras,
                cmd=self.cmd)

        command = utils.format_command(command)
        return command

    def auth(self):
        if self.passwords:
            for password in self.passwords:
                r = self.p.expect([pexpect.TIMEOUT, '[p|P]assword:'])
                if r == 0:
                    logger.error(c.MSG_CONNECTION_TIMED_OUT)
                    return False
                self.p.sendline(password)
        return True

    def drain_child_buffer(self):
        '''Read all data from child to make it eof.'''
        try:
            data = self.p.read_nonblocking(size=100, timeout=1)
            while data:
                data = self.p.read_nonblocking(size=100, timeout=1)
        except (pexpect.EOF, pexpect.TIMEOUT):
            logger.debug('drain buffer to EOF')

    def daemonize(self):
        '''Detach the process.
        Return True in parent process, False in child.
        '''
        import os
        pid = os.fork()
        if pid == 0:
            # child
            logger.debug('Run in child daemon.')

            # import sys
            # fd = os.open(os.devnull, os.O_RDWR | os.O_CREAT)
            # os.dup2(fd, sys.stdin.fileno())
            # os.dup2(fd, sys.stdout.fileno())
            # os.dup2(fd, sys.stderr.fileno())
            return False
        return True

    def interactive(self):
        p = self.p
        if self.background:
            if self.execute:
                p.interact(escape_character=None)
            else:
                self.drain_child_buffer()
        else:
            set_winsize(p)  # Adjust window size
            # Set auto-adjust window size
            signal.signal(signal.SIGWINCH, sigwinch_passthrough(p))

            # r = p.expect([pexpect.TIMEOUT, '\S'])
            # if r == 1:
            #     p.write_to_stdout(p.after)

            # find the first non-empty character
            # block forever if not found
            p.expect('\S', timeout=None)
            p.write_to_stdout(p.after)

            p.interact(escape_character=None)
        return STATUS_SUCCESS

    def run(self):
        self.command = self.compile_command()

        logger.debug(self.command)
        self.start_process()

    def start_process(self):
        if self.detach:
            if self.daemonize():
                return STATUS_SUCCESS

        try:
            self.p = pexpect.spawn(self.command)

            if not self.auth():
                logger.error(c.MSG_AUTH_FAILED)
                return STATUS_FAIL

            return self.interactive()
        except Exception as e:
            logger.error(c.MSG_CONNECTION_ERROR)
            logger.debug(e)
            return STATUS_FAIL


class SCPPexpect(SSHPexpect):
    def __init__(self, account, targets, vias):
        self.account = account
        self.targets = targets
        self.vias = vias

        self.background = False
        self.detach = False

        self.p = None

    def compile_command(self):
        account = self.account
        self.jump, self.passwords = compile_jumps(
            account, vias=self.vias, prefix='-oProxyJump=')

        if not self.account.identity:
            self.passwords.append(self.account.password)

        src, dst = self.targets.compile()

        if account.identity:
            command = _SCP_COMMAND_IDENTITY.format(
                jump=self.jump,
                port=account.port,
                src=src,
                dst=dst,
                identity=account.identity)
        else:
            command = _SCP_COMMAND_PASSWORD.format(
                jump=self.jump,
                port=account.port,
                src=src,
                dst=dst)
        command = utils.format_command(command)
        return command


class SCPPexpect2(SCPPexpect):
    def __init__(self, account, targets, vias):
        super().__init__(account, targets, vias)
        self.forwarding = None

    def create_forwarding(self):
        account = self.account
        jumps = find_vias(self.vias) if self.vias else find_jumps(account)

        if jumps:
            jump1 = jumps.pop()
            self.host = LOCALHOST
            self.port = find_available_port()
            maps = f'{self.host}:{self.port}:{account.host}:{account.port}'
            forwards = Forwards(maps, '')

            vias = ','.join([a.name for a in jumps])
            self.forwarding = SSHPexpect(
                jump1, vias=vias, forwards=forwards,
                tty=False, background=True, execute=False)

    def compile_command(self):
        account = self.account
        self.port = account.port
        self.host = account.host
        self.passwords = [account.password]

        self.create_forwarding()

        src, dst = self.targets.compile(src_host=self.host, dst_host=self.host)

        if account.identity:
            command = _SCP_COMMAND_IDENTITY.format(
                jump='',
                port=self.port,
                src=src,
                dst=dst,
                identity=account.identity)
        else:
            command = _SCP_COMMAND_PASSWORD.format(
                jump='',
                port=self.port,
                src=src,
                dst=dst)
        command = utils.format_command(command)
        return command

    def run(self):
        self.command = self.compile_command()

        if self.forwarding:
            logger.debug('start forwarding')
            self.forwarding.run()

        logger.debug(self.command)
        self.start_process()

        if self.forwarding:
            logger.debug('stop forwarding')
            utils.kill_by_command(self.forwarding.command)


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


def ssh(account, vias=None, forwards=None, extras='', detach=False,
        tty=True, background=False, execute=True, cmd=''):
    p = SSHPexpect(account,
                   vias=vias, forwards=forwards, extras=extras, detach=detach,
                   tty=tty, background=background, execute=execute, cmd=cmd)
    return p.run()


def scp(account, targets, vias=None, with_forward=False):
    klass = SCPPexpect2 if with_forward else SCPPexpect
    p = klass(account, targets, vias)
    return p.run()
