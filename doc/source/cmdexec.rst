Execute command
===============

``sshx exec`` execute an remote command. The arguments after ``--`` is the command line to be executed remotely.

Execute ``ls -al`` on host1. ::

    sshx exec host1 -- ls -al

Execute an command with tty. ::

    sshx exec host1 --tty -- /bin/bash

Execute an command on host1 via host2. ::

    sshx exec host1 -v host2 -- ls -al
