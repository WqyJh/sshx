Update accounts
===============

``sshx update`` updates an account. The supported options are the same with ``add`` command, all the specified fields will be updated.

Change the host1's ``host`` field to ``domain.com``. ::

    sshx update host1 -H domain.com

Change the host1's ``password``. This would ask password from prompt. ::

    sshx update host1 -p

Set/Change the host1's identity to ``identity2``. This would ask passphrase from prompt if it had. ::

    sshx update host1 -i identity2

Rename host1 to host2. ::

    sshx update host1 -n host2

Unset the host1's identity. This would ask user to set and password if it's never been set. ::

    sshx update host1 -i ''
