Quick Start
===========

Install
-------

.. code-block:: bash

    sudo pip3 install sshx


Initialization
--------------

Perform only once after you've installed sshx.

.. code-block:: bash

    sshx init


Adding an account
-----------------

.. code-block:: bash

    sshx add myhost -l test@192.168.9.155

This command will ask you to type your password and sshx would store the encrypted password.


Connect to the account
----------------------

.. code-block:: bash

    sshx connect myhost

