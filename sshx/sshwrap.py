import os
import sys
import uuid
import time
import struct
import termios
import signal
import fcntl
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
-o LogLevel=ERROR \
-o StrictHostKeyChecking=no \
-o UserKnownHostsFile=/dev/null \
-oExitOnForwardFailure=yes \
{extras} {forwards} {jump} -p {port} {user}@{host} {cmd}'
_SSH_COMMAND_IDENTITY = 'ssh \
-o LogLevel=ERROR \
-o StrictHostKeyChecking=no \
-o UserKnownHostsFile=/dev/null \
-oExitOnForwardFailure=yes \
-i {identity} {extras} {forwards} {jump} -p {port} {user}@{host} {cmd}'
_SSH_CONFIG_GLOBAL = '''Host *
\tLogLevel ERROR
\tStrictHostKeyChecking no
\tUserKnownHostsFile /dev/null
\tExitOnForwardFailure yes
'''
_SSH_COMMAND_CONFIG = 'ssh {extras} {forwards} {name} {cmd}'
_SSH_DEST = '{user}@{host}:{port}'
_SCP_COMMAND_PASSWORD = 'scp -r \
-oPreferredAuthentications=password \
-o LogLevel=ERROR \
-oStrictHostKeyChecking=no \
-oUserKnownHostsFile=/dev/null \
-oExitOnForwardFailure=yes \
{jump} -P {port} {src} {dst}'
_SCP_COMMAND_IDENTITY = 'scp -r \
-o LogLevel=ERROR \
-oStrictHostKeyChecking=no \
-oUserKnownHostsFile=/dev/null \
-oExitOnForwardFailure=yes \
-i {identity} {jump} -P {port} {src} {dst}'
_SCP_COMMAND_CONFIG = 'scp {extras} {src} {dst}'


class AccountChain(object):
    def __init__(self, account, vias=None):
        self.chain = self._get_chain(account, vias=vias)
        self.config_file = None

    def __del__(self):
        if self.config_file:
            try:
                logger.debug(f'deleting {self.config_file}')
                os.remove(self.config_file)
            except OSError as e:
                logger.warning(
                    f'error occurred while deleting {self.config_file}:\n{e}')

    def _get_chain(self, account, vias=None):
        if vias:
            chain = [cfg.config.get_account(v, decrypt=True)
                     for v in vias.split(',')]
            chain.append(account)

            for i in range(1, len(chain)):
                chain[i].via = chain[i - 1].name
        else:
            chain = []
            a = cfg.config.get_account(account.via, decrypt=True)
            while a:
                chain.append(a)
                a = cfg.config.get_account(a.via, decrypt=True)
            chain.append(account)

        return chain

    def get_jump(self, prefix='-J '):
        dests = [_SSH_DEST.format(user=a.user, host=a.host, port=a.port)
                 for a in self.chain[:-1]]
        jump = (prefix + ','.join(dests)) if dests else ''
        return jump

    def get_passwords(self):
        passwords = []
        for a in self.chain:
            if not a.identity:
                passwords.append(a.password)
            elif a.passphrase:
                passwords.append(a.passphrase)
        return passwords

    def has_identity(self):
        return any(map(lambda a: a.identity, self.chain))

    def need_config(self):
        if len(self.chain) > 1:
            for a in self.chain[:-1]:
                if a.identity:
                    return True
        return False

    def get_config(self):
        config_list = [_SSH_CONFIG_GLOBAL] + \
            [a.to_ssh_config() for a in self.chain]
        config = '\n'.join(config_list)
        self.config_file = os.path.join(cfg.CONFIG_DIR, str(uuid.uuid4()))
        with open(self.config_file, 'w') as f:
            config = config.format(config=self.config_file)
            logger.debug(config)
            f.write(config)
        return self.config_file


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
        self.chain = AccountChain(self.account, vias=self.vias)
        self.jump = self.chain.get_jump()
        self.passwords = self.chain.get_passwords()

        self.extras += self.compile_flags()

        # keep alive config
        if ServerAliveInterval > 0:
            self.extras += f' -o ServerAliveInterval={ServerAliveInterval} -o ServerAliveCountMax={ServerAliveCountMax}'

        # port forwarding config
        self._forwards = self.forwards.compile() if self.forwards else ''

        if self.chain.need_config():
            command = self.compile_config_command()
        else:
            command = self.compile_pure_command()
        command = utils.format_command(command)
        return command

    def compile_pure_command(self):
        account = self.account
        if account.identity:
            command = _SSH_COMMAND_IDENTITY.format(
                jump=self.jump,
                forwards=self._forwards,
                user=account.user,
                host=account.host,
                port=account.port,
                identity=account.identity,
                extras=self.extras,
                cmd=self.cmd)
        else:
            command = _SSH_COMMAND_PASSWORD.format(
                jump=self.jump,
                forwards=self._forwards,
                user=account.user,
                host=account.host,
                port=account.port,
                extras=self.extras,
                cmd=self.cmd)
        return command

    def compile_config_command(self):
        config = self.chain.get_config()
        self.extras += f' -F {config}'

        command = _SSH_COMMAND_CONFIG.format(
            forwards=self._forwards,
            extras=self.extras,
            name=self.account.name,
            cmd=self.cmd)
        return command

    def auth(self):
        if self.passwords:
            it = iter(self.passwords)
            password = next(it)
            while True:
                r = self.p.expect([
                    pexpect.TIMEOUT,
                    "(?i)are you sure you want to continue connecting",
                    '[p|P]assword:', r'passphrase for key[\s\S]+?:'])
                if r == 0:
                    logger.error(c.MSG_CONNECTION_TIMED_OUT)
                    return False
                if r == 1:
                    self.p.sendline('yes')
                    continue

                self.p.sendline(password)
                try:
                    password = next(it)
                except StopIteration:
                    break
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

    def run(self, retry=0, retry_interval=5):
        if self.detach:
            if self.daemonize():
                return STATUS_SUCCESS

        self.command = self.compile_command()
        logger.debug(self.command)

        _try = 0
        while True:
            ret = self.start_process()
            if ret == STATUS_SUCCESS:
                return STATUS_SUCCESS

            if retry == 'always' or retry > 0:
                if retry == 'always' or _try < retry:
                    _try += 1
                    logger.info(
                        f'failed, sleep {retry_interval}s before retry.')
                    time.sleep(retry_interval)
                    logger.info(f'retry: {_try}')
                    continue
                logger.error('still failed, please check the network.')
            break

    def start_process(self):
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
        self.extras = ''

        self.background = False
        self.detach = False

        self.p = None

    def compile_command(self):
        self.chain = AccountChain(self.account, vias=self.vias)
        self.jump = self.chain.get_jump(prefix='-oProxyJump=')
        self.passwords = self.chain.get_passwords()

        if self.chain.need_config():
            command = self.compile_config_command()
        else:
            command = self.compile_pure_command()
        command = utils.format_command(command)
        return command

    def compile_pure_command(self):
        account = self.account
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
        return command

    def compile_config_command(self):
        src = self.targets.src.raw
        dst = self.targets.dst.raw
        config = self.chain.get_config()
        self.extras += f' -F {config}'

        command = _SCP_COMMAND_CONFIG.format(
            extras=self.extras,
            name=self.account.name,
            src=src, dst=dst)
        return command


class SCPPexpect2(SCPPexpect):
    '''scp -v a,b,c src d:dst
    Split to two steps:
    step 1.
    forward -v a,b c -f lhost:lport:d.host:d.port
    step 2.
    scp -P lport src d.user@lhost:dst
    '''

    def __init__(self, account, targets, vias):
        super().__init__(account, targets, vias)
        self.forwarding = None

    def create_forwarding(self):
        account = self.account
        self.chain = AccountChain(self.account, vias=self.vias)
        jumps = self.chain.chain[:-1]

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
        self.host = account.host
        self.port = account.port

        # May change self.host to LOCALHOST if has jumps
        self.create_forwarding()

        account.via = ''
        self.chain = AccountChain(account)
        self.passwords = self.chain.get_passwords()

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
        return self.start_process()

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
        tty=True, background=False, execute=True, cmd='',
        retry=0, retry_interval=5):
    p = SSHPexpect(account,
                   vias=vias, forwards=forwards, extras=extras, detach=detach,
                   tty=tty, background=background, execute=execute, cmd=cmd)
    return p.run(retry=retry, retry_interval=retry_interval)


def scp(account, targets, vias=None, with_forward=False):
    klass = SCPPexpect2 if with_forward else SCPPexpect
    p = klass(account, targets, vias)
    return p.run()
