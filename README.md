# sshx (SSH with account managing)

[![Build Status](https://travis-ci.org/WqyJh/sshx.svg?branch=master)](https://travis-ci.org/WqyJh/sshx)
[![codecov](https://codecov.io/gh/WqyJh/sshx/branch/master/graph/badge.svg)](https://codecov.io/gh/WqyJh/sshx)
[![license](https://img.shields.io/badge/LICENCE-GPLv3-brightgreen.svg)](https://raw.githubusercontent.com/WqyJh/sshx/master/LICENSE)


sshx is a lightweight ssh client with account managing. You can assign names to your accounts and connect with the name, without input the username, host, port, password, identity.

## Installation

### Install from pypi

For **Windows**:

```bash
pip install --extra-index-url https://wqyjh.github.io/python-wheels/ sshx
```

For **Linux**, **macOS**:

```bash
pip install sshx
```

### Install from source

For **Windows**:
```bash
pip install --extra-index-url https://wqyjh.github.io/python-wheels/ git+https://github.com/WqyJh/sshx

# Or

pip install -i index-url https://wqyjh.github.io/python-wheels/ pyHook
python setup.py install

# Or

pip install -r requirements.txt
```

For **Linux**, **macOX**:
```bash
pip install git+https://github.com/WqyJh/sshx

# Or

python setup.py install

# Or

pip install -r requirements.txt
```


## Quick Start

1. Initialization.

```bash
sshx init
```

2. Adding an account.

```bash
sshx add myhost -H 192.168.9.155 -u test
```

(This command will ask you to type your password and sshx would store the encrypted password.)

3. Connect to the account.

```bash
sshx connect myhost
```

## Usage

**`sshx init`**

Create the following files which storing the account info. If the files are damaged you'll probably 
lost all the accounts, so **DON'T TOUCH IT**. If this happened, use this command to re-init and use
`add` command to re-add them.

```bash
~/.sshx
└── .accounts
```

**`sshx add`**

```bash
# add an account and specify an password for authentication
sshx add myhost -H host -P port -u user -p

# add an account and specify an identity file for authentication
sshx add myhost -H host -P port -u user -i identity_file

# add an account and specify both password and identity file for authentication
sshx add myhost -H host -P port -u user -p -i identity_file
```

- Host and user option are required for adding an account.
- Either a password or a identity option is required for adding an account. You can also specify both of them for an account. In this case, only using identity for authentication(maybe improved later).
- Password are input from the prompt, which won't show in the screen.

**`sshx list`**

List all the accounts as the following format.

```bash
name                          host                          user
------------------------------------------------------------------------------------------
host1                         192.168.9.188                 user1
host2                         192.168.9.155                 user2
host3                         192.168.9.156                 user3
test                          192.168.9.157                 user4
```

**`sshx del`**

Delete an account.

```bash
sshx del host1
```

**`sshx update`**

Update an account.

The arguments list is same with `add` command, all the specified fields will be updated.

```bash
# change the host1's host field to domain.com
sshx update host1 -H domain.com

# change the host1's password
sshx update host1 -p

# change the host1's identity to identity2
sshx update host1 -i identity2

# change the host1's name to host2, and the next time you want to 
# change the account you have to use `sshx update host2 ...`
sshx update host1 -n host2
```

**`sshx connect`**

Connect to an account.

```bash
sshx connect host1
```

## Test

```bash
python setup.py test
```

## Todo

- scp support
- jump host support
- X11Forward support(test)