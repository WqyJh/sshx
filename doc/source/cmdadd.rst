Add accounts
============

``sshx add`` adds an account.


Usage: ::

    Usage: sshx add [OPTIONS] NAME

    Add an account and assign a name for it.

    Options:
    -l TEXT              <user>@<host>[:port]
    -H, --host TEXT
    -P, --port TEXT
    -u, --user TEXT
    -p, --password
    -i, --identity TEXT  SSH identity file.
    -v, --via TEXT       Account name of jump host.
    --help               Show this message and exit.


Add an account and specify an password for authentication. ::

    sshx add myhost -H host -P port -u user -p

Add an account in an simple way. ::

    sshx add myhost -l user@host:port

Add an account and specify an identity file for authentication. This may ask you to input the passphrase from prompt if the identity file has one. ::

    sshx add myhost -H host -P port -u user -i identity_file

Add an account and specify both password and identity file for authentication. In this situation, only identity file would be used for authentication. ::

    sshx add myhost -H host -P port -u user -p -i identity_file


.. _JumpHost:

Jump hosts
----------

Jump hosts are intermediate hosts for establishing SSH connections.

Assume you have an server A in an internal network, and you cannot access it directly, but you have an server B, which you can access directly and B can access A, then you can connect server A via server B, while the server B is a jump host.

Add an account and specify an jump host for it. ::

    sshx add -l user@host:port -v myhost myhost2

After the account with jump host was added, you can connect it by ``sshx connect myhost2``, an ssh connection to ``myhost2`` would be established via the jump host ``myhost``.

You can specify multiple jump hosts for an single account, which are seperated by comma characters. ::

    sshx add -l user@host:port -v myhost1,myhost2,myhost3 myhost4

Jump hosts would be visited sequentially. For example, connect to ``myhost1``, then connect to ``myhost2`` by ``myhost1``, then connect to ``myhost3`` by ``myhost2``, finally connect to ``myhost4`` by ``myhost3``.

The jump hosts would be translated to ``-J``, ``ProxyJump`` or ``ProxyCommand`` options of ``ssh`` command.
