Copy files
==========

``sshx scp`` copy files to/from servers.

Copy local directory ``/tmp/dir`` to host1's ``/tmp``. ::

    sshx scp /tmp/src host1:/tmp

Copy remote files from host1 to local. ::

    sshx scp host1:/tmp/src /tmp

Copy local files to host1 with host2 as jump host. ::

    sshx scp /tmp/src host1:/tmp -v host2

Copy remote files to local, using host2 as jump host and using host3 as host2's jump host. ::

    sshx scp host1:/tmp/src /tmp -v host2,host3
