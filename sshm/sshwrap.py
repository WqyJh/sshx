from __future__ import unicode_literals

import paramiko
from .interactive import interactive_shell


def sshp(host, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, int(port), user, password)
    chan = client.invoke_shell()
    interactive_shell(chan)


def sshi(host, port, user, identity):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, int(port), user, key_filename=identity)
    chan = client.invoke_shell()
    interactive_shell(chan)


if __name__ == '__main__':
    # sshp('domain', port, 'user', 'password')
    sshi('domain', 'port', 'user', '/path/to/id_rsa')
