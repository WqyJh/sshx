Install public keys
===================

``sshx copyid`` installs public keys (``*.pub``) to remote hosts.

Assume you have an account host1 using password for authentication. Now you want to change it to use public key ``id_rsa.pub`` for authentication. You can achieve this by two steps.

Step 1: copy public key to the host1. ::

    sshx copyid id_rsa.pub host1

Step 2: set the corresponding identity to the account. ::

    sshx update host1 -i id_rsa

You can also install public keys via jump hosts. ::

    sshx copyid id_rsa.pub host1 -v host2
