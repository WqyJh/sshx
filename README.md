# sshx (SSH eXtensions)

[![Build Status](https://travis-ci.org/WqyJh/sshx.svg?branch=master)](https://travis-ci.org/WqyJh/sshx)
[![codecov](https://codecov.io/gh/WqyJh/sshx/branch/master/graph/badge.svg)](https://codecov.io/gh/WqyJh/sshx)
[![license](https://img.shields.io/badge/LICENCE-GPLv3-brightgreen.svg)](https://raw.githubusercontent.com/WqyJh/sshx/master/LICENSE)
[![Docs Status](https://readthedocs.org/projects/sshx/badge/?version=latest)](https://readthedocs.org/projects/sshx/badge/?version=latest)


sshx is a lightweight wrapper for ssh/scp command, which has the following features:
- Remember your ssh account
- Connect to your account with a short command, without typing password
- Enable jump host for your connection
- Create ssh forwarding with a short command, without typing password
- Create socks5 proxy from ssh dynamic port forwarding
- Enable jump host for your port forwarding
- Copy files from/to your account with a short command, without typing password
- Enable jump host for your scp connection

Read full documentation on [ReadTheDocs](https://sshx.readthedocs.io/en/latest/).


## Installation

```bash
pip install sshx
```

### Supported platform

- Linux
- macOS
- WSL/cygwin/msys2 on Windows

**Attention:**
- Native Windows support was removed.
- Python 2 support was removed.

### Requirements

- Python >= 3.6
- openssh-clients: `ssh`, `scp`, `ssh-keygen`


## Quick Start

1. Initialization.

    Perform only once after you've installed sshx.

    ```bash
    sshx init
    ```

2. Adding an account.

    ```bash
    sshx add myhost -l test@192.168.9.155
    ```

    (This command will ask you to type your password and sshx would store the encrypted password.)

3. Connect to the account.

    ```bash
    sshx connect myhost
    ```

