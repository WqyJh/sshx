Installation
============

sshx is on PyPI, and can be installed with pip::

    pip install sshx


Supported platforms
-------------------
- Linux
- macOS
- WSL/cygwin/msys2 on Windows
- Termux on Android

**Attention:**

- Windows CMD/PowerShell support was removed.
- Python 2 support was removed.


Requirements
------------
- Python >= 3.6
- openssh-clients: ``ssh``, ``scp``, ``ssh-keygen``


Install on Android
------------------

First install latest Termux app (tested version 0.92) on your android device.

Then install some requirements on termux shell. ::

    pkg update
    pkg in python openssh
    pip install sshx
