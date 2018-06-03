from __future__ import unicode_literals

import paramiko
from .interactive import interactive_shell

from . import utils

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


def ssh(host, port, user, password='', identity=''):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if identity:
        f = lambda: client.connect(host, int(port), user, key_filename=identity)
        use_password = False
    else:
        f = lambda: client.connect(host, int(port), user, password=password)
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



if __name__ == '__main__':
    ssh('domain', 'port', 'user', password='password', identity='/path/to/id_rsa')
