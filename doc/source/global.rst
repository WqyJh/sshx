Global Options
================

.. code-block:: bash

    Usage: run.py [OPTIONS] COMMAND [ARGS]...

    Options:
    --version                       Show the version and exit.
    -d, --debug
    --interval INTEGER RANGE        ServerAliveInterval for ssh_config.
    --countmax INTEGER RANGE        ServerAliveCountMax for ssh_config.
    --forever                       Keep ssh connection forever.
    --retry RETRY                   Reconnect after connection closed, repeat
                                    for retry times. Supported values are
                                    "always" or non negative integer. If retry
                                    was enabled, --interval must be greater than
                                    0.
    --retry-interval INTEGER RANGE  Sleep seconds before every retry.
    --help                          Show this message and exit.


Global options must be specified before sub-commands.

The ``--retry`` and ``--retry-interval`` options can only be used for ``connect``, ``forward``, ``socks`` and ``exec`` commands.

Create a socks5 proxy and always reconnect immediately when the connection was closed. ::

    sshx --interval 1 --countmax 1 --retry always socks host1

Create a socks5 proxy and always reconnect after 5s when the connection was closed. ::

    sshx --interval 1 --countmax 1 --retry always --retry-interval 5 socks host1

Create a socks5 proxy and reconnect for 5 times when the connection was close. ::

    sshx --interval 1 --countmax 1 --retry 5 socks host1

Create a ssh connection and set the ``ServerAlive`` options. The following options make the ssh client
sends a keepalive probe to server after no data was transfered for 30s and after probing for 60
times the connection would be closed (idle for 1800s). ::

    sshx --interval 30 --countmax 60 connect host1

The ``--forever`` option is an alias for ``--interval 60 --countmax 52560000``, which means the ssh connection would be closed after idle for 100 years (long enough :). You can also set a value longer than ``--forever``.

.. note:: The ``forever`` option is now a default option, which improves user experience.
