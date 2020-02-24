Initialization
==============

``sshx init`` performs initialization. ::

    $ sshx init
    $ tree ~/.sshx
    ~/.sshx
    └── .accounts

It will create the config file ``~/.sshx/.accounts`` which stores the accounts info.

If the config files are damaged you'll probably lost all the accounts added, so **DON'T TOUCH IT**.


Customize config location
-------------------------

You can set environment variable ``SSHX_HOME`` to customize the location of config files, the default value is ``~/.sshx``.


Config file format
------------------

The passwords of accounts and passphrases of identities are stored encrypted.

The ``phrase`` field is a string randomly generated during initialization to encrypt and decrypt the passwords of accounts and the passphrase of identities.

It's **very important** to keep the config file save, otherwise your passwords may leak.

Want more secure, see `Security Option`_

.. code-block:: json

    {
        "security": false,
        "phrase": "acnhPz21bUfx1PE",
        "accounts": [
            {
                "name": "host1",
                "user": "root",
                "host": "172.17.0.2",
                "port": "22",
                "password": "InJvb3Qi.gM0vblkle9Utv5NrW6Q_WzZEgSg",
                "identity": "",
                "passphrase": "",
                "via": ""
            },
            {
                "name": "host2",
                "user": "root",
                "host": "192.168.0.6",
                "port": "22",
                "password": "InJvb3Qi.gM0vblkle9Utv5NrW6Q_WzZEgSg",
                "identity": "",
                "passphrase": "",
                "via": ""
            }
        ]
    }


Force initialization (Dangerous)
--------------------------------

Delete the previous config files and perform initialization. ::

    sshx init --force

If it's previous inited, ``sshx init`` would failed which protect the config file from being damaged.

Only if you're sure you don't need the existing accounts anymore, you could add this option.

``--force`` option can be used with ``--security`` option.


.. _SecurityOption:

Security Option
---------------

Enable security option during initialization: ::

    sshx init --security

This option will ask you to set a ``phrase`` manually for encryption and decryption. The ``phrase`` won't be stored in the config file, instead the SHA1 hash of it would be stored for verification.

If the security option was enabled, you would be asked to input the ``phrase`` from prompt every you execute a command of sshx that need to access the encrypted data.


This option could be changed after initialization.

Enable security option. This will ask you to set a ``phrase`` and re-encrypt all sensitive data. ::

    sshx config --security-on

Disable security option. This will ask ``phrase`` from prompt for verification, generate a new random phrase and re-encrypt all sensitive data. ::

    sshx config --security-off

Change ``phrase``: If security option was disabled, re-generate a random phrase, otherwise it would ask user to input the current ``phrase``, verify it and ask user to set a new ``phrase``. ::

    sshx config --chphrase
