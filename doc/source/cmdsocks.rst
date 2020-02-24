Create socks5 proxies
=====================

``sshx socks`` creates socks5 proxies by ssh's ``DynamicForward`` option. When you connect to an server by ssh with this option, the ssh client would establish an socks5 server locally, just like the ``shadowsocks`` client, while the connected ssh server would perform the requests for you, just like the ``shadowsocks`` server.

Why create socks5 proxies with ssh? Because it's very simple and safe.

- Simple: no need for extra softwares, easy to config and use.
- Safe: all traffic would be carried and encrypted by ssh, safer than ``shadowsocks``.


Create an socks5 proxy listening on ``127.0.0.1:1080``. ::

    sshx socks host1

Customize the listening address with ``--bind`` option. ::

    sshx socks host1 --bind 0.0.0.0:1081

Create socks proxy with jump hosts. ::

    sshx socks host1 -v host2,host3

Run in background with ``-b`` option. ::

    sshx socks host1 -b


Configuration
-------------

The ssh server must enable ``AllowTcpForwarding`` option which is enabled by default. Therefore, no need to set it manually.

If you could connect to the server but cannot establish an socks5 proxy, then consider to enable this option in ``/etc/ssh/sshd_config`` on the server.
