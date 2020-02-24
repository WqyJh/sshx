sshx version |version|
======================

.. image:: https://travis-ci.org/WqyJh/sshx.svg?branch=master
   :target: https://travis-ci.org/WqyJh/sshx
   :alt: Build status

.. image:: https://codecov.io/gh/WqyJh/sshx/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/WqyJh/sshx
   :alt: Code Coverage

.. image:: https://img.shields.io/badge/LICENCE-GPLv3-brightgreen.svg
   :target: https://raw.githubusercontent.com/WqyJh/sshx/master/LICENSE
   :alt: License

sshx is a lightweight wrapper for ssh/scp command, which has the following features:

- Remember your ssh accounts safely.
- Connect to your account without typing password.
- Set jump hosts for your connection.
- Create ssh port forwardings without typing password.
- Create socks5 proxy by ssh dynamic port forwarding.
- Enable jump hosts for your port forwardings.
- Copy files from/to your account without typing password.
- Enable jump hosts for your scp connection.
- Execute remote command without typing password.
- Enable jump hosts for executing command.
- Install ssh public keys to remote server.
- Enable jump hosts for public key installation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   quickstart
   initialization
   cmdadd
   cmdshow
   cmddel
   cmdupdate
   cmdconnect
   cmdsocks
   cmdforward
   cmdscp
   cmdexec
   cmdcopyid
   global
   dev



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
