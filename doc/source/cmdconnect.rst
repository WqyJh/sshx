Connect accounts
================

``sshx connect`` connect to an account.

Connect host1 directly. ::

    sshx connect host1

Connect host1 using host2 as jump host. If the host1 already had an jump host, this would temporarily override it. ::

    sshx connect host1 -v host2

Connect to host1 using host2 as jump host, while the host2 is using host3 as jump host. This is also a temporary jump host, which won't affect the config files. ::

    sshx connect host1 -v host2,host3

If the host3 was already had host2 as its jump host, then the following command is equivalent to the above one. ::

    sshx connect host1 -v host3

You can specify extra arguments for ssh, which would be added into the ssh command line.

For example, add verbose option. ::

    sshx connect host1 -e '-v'


X11Forwarding
-------------

The ssh server must have the following config on ``/etc/ssh/sshd_config``. ::

    X11Forwarding yes
    X11UseLocalhost no

Connect to host1 and enable ``X11Forwarding``. ::

    sshx connect host1 -e '-X'

Then you can execute graphical program like ``gedit`` on the shell, and the
window would show on your local screen.
