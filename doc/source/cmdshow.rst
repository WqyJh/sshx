Show accounts
=============

List accounts
-------------

``sshx list`` lists all the accounts in the following format. ::

    name                host                          user                via                 
    -----               -----                         -----               -----               
    host1               192.168.7.1                   root                                    
    host2               192.168.7.2                   test                host1               
    host3               192.168.7.3                   root                host2               

The outputs can be sorted and reversed.

Usage: ::

    Usage: sshx list [OPTIONS]

    List all accounts.

    Options:
    --sort [name|host|user]  Sort by keys.
    --reverse
    --help                   Show this message and exit.



Show account detail
-------------------

``sshx show`` show details for a specified account.

Show account info (without encrypted data). ::

    sshx show host1

Show account info with data decrypted. (Need to input ``phrase`` if :ref:`SecurityOption` was enabled.) ::

    sshx show host2 -p
