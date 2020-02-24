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
