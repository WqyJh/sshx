Create port forwardings
=======================

``sshx forward`` creates port fowardings. ::

    Usage: sshx forward [OPTIONS] NAME

    SSH port forward via specified account.

    Options:
    -v, --via TEXT            Account name of jump host.
    -L, -f, --forward TEXT    [bind_address]:<bind_port>:<remote_address>:<remot
                                e_port> => Forward local bind_address:bind_port to
                                remote_address:remote_port.
    -R, -rf, --rforward TEXT  <bind_address>:<bind_port>:<local_address>:<local_
                                port> => Forward remote bind_address:bind_port to
                                local local_address:local_port.
    -b, --background          Run in background.
    --help                    Show this message and exit.

Forward ``localhost:80`` to ``192.168.77.7:80``, while the host1 is the intermedia server, so you must ensure the host1 could connect to ``192.168.77.7:80``. ::

    sshx forward host1 -L :80:192.168.77.7:80

Forward ``host1:8000`` to ``192.168.99.9:8000``. When you access ``localhost:8000`` on host1, the connection would be forward to ``192.168.99.9:8000``, while your computer is working as a intermediate server, so you have to ensure your computer has access to ``192.168.99.9:8000``. ::

    sshx forward host1 -R :8000:192.168.99.9:8000

Specify multiple forwards. The following command sets two local forwards and one remote forward. ::

    sshx forward host1 -L :80:192.168.77.7:80 :8080:192.168.77.7:8080 -R :8000:192.168.99.9:8000


Forward can also be used with jump hosts. ::

    sshx forward host1 -v host2 -L :80:192.168.77.7:80

