from __future__ import unicode_literals

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

if not utils.PY3:
    FileNotFoundError = IOError

if utils.NT:
    from pykeyboard import PyKeyboard


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


def _ssh_paramiko(host, port, user, password='', identity=''):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if identity:
        def f(): return client.connect(host, int(port), user, key_filename=identity)
        use_password = False
    else:
        def f(): return client.connect(host, int(port), user, password=password)
        use_password = True
    msg = _connect(f, use_password)

    if msg['status'] == 'success':
        chan = client.invoke_shell()
        interactive_shell(chan)
        return {
            'status': 'success',
            'msg': 'Connection to %s closed.' % host,
        }
    else:
        return msg


def set_winsize(p):
    s = struct.pack("HHHH", 0, 0, 0, 0)
    a = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ , s))

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


def _ssh_pexpect(host, port, user, password='', identity=''):
    from pexpect import pxssh
    s = pxssh.pxssh(options=dict(StrictHostKeyChecking="no", UserKnownHostsFile="/dev/null"))

    if identity:
        s.login(host, user, port=port, ssh_key=identity, auto_prompt_reset=False)
    else:
        s.login(host, user, port=port, password=password, auto_prompt_reset=False)

    set_winsize(s) # Adjust window size
    signal.signal(signal.SIGWINCH, sigwinch_passthrough(s)) # Set auto-adjust window size

    # If don't send an '\n', users have to press enter manually after
    # interact() is called
    s.send('\x1b\x00')
    s.interact()


_SSH_COMMAND_PASSWORD = 'ssh {user}@{host} -p {port} \
                        -o PreferredAuthentications=password \
                        -o StrictHostKeyChecking=no \
                        -o UserKnownHostsFile=/dev/null'
_SSH_COMMAND_IDENTITY = 'ssh {user}@{host} -p {port} -i {identity}'


def _ssh_command_password(host, port, user, password='', identity=''):
    def input_password(password):
        # delay 1s
        time.sleep(1)
        # input password
        k = PyKeyboard()
        k.type_string(password)
        k.tap_key(k.enter_key)

    threading.Thread(target=input_password, args=(password,)).start()
    try:
        command = _SSH_COMMAND_PASSWORD.format(
            host=host, port=port, user=user).split()
        return subprocess.call(command)
    except Exception:
        sys.stdin.flush()


def _ssh_command(host, port, user, password='', identity=''):
    if utils.NT:
        if identity:
            command = _SSH_COMMAND_IDENTITY.format(
                host=host, port=port, user=user, identity=identity).split()
            return subprocess.call(command)
        else:
            _ssh_command_password(host, port, user, password)
    else:
        _ssh_pexpect(host, port, user, password=password, identity=identity)


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


def ssh(host, port, user, password='', identity=''):
    if has_command('ssh'):
        return _ssh_command(host, port, user, password=password, identity=identity)
    else:
        return _ssh_paramiko(host, port, user, password=password, identity=identity)


if __name__ == '__main__':
    ssh('huawei', 'port', 'user', password='password', identity='/path/to/id_rsa')
