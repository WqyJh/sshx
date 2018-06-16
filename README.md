# sshm (SSH with account managing)

[![Build Status](https://travis-ci.org/WqyJh/sshm.svg?branch=master)](https://travis-ci.org/WqyJh/sshm)
[![codecov](https://codecov.io/gh/WqyJh/sshm/branch/master/graph/badge.svg)](https://codecov.io/gh/WqyJh/sshm)
[![license](https://img.shields.io/badge/LICENCE-GPLv3-brightgreen.svg)](https://raw.githubusercontent.com/WqyJh/sshm/master/LICENSE)


sshm is a lightweight ssh client with account managing. You can assign names to your accounts and connect with the name, without input the username, host, port, password, identity.

## Installation

```bash
pip install sshm
```

## Quick Start

1. Initialization.

```bash
sshm init
```

2. Adding an account.

```bash
sshm add myhost -H 192.168.9.155 -u test
```

(This command will ask you to type your password and sshm would store the encrypted password.)

3. Connect to the account.

```bash
sshm connect myhost
```

## Usage

**`sshm init`**

Create the following files which storing the account info. If the files are damaged you'll probably 
lost all the accounts, so **DON'T TOUCH IT**. If this happened, use this command to re-init and use
`add` command to re-add them.

```bash
~/.sshm
└── .accounts
```

**`sshm add`**

```bash
# add an account and specify an password for authentication
sshm add myhost -H host -P port -u user -p

# add an account and specify an identity file for authentication
sshm add myhost -H host -P port -u user -i identity_file

# add an account and specify both password and identity file for authentication
sshm add myhost -H host -P port -u user -p -i identity_file
```

- Host and user option are required for adding an account.
- Either a password or a identity option is required for adding an account. You can also specify both of them for an account. In this case, only using identity for authentication(maybe improved later).
- Password are input from the prompt, which won't show in the screen.

**`sshm list`**

List all the accounts as the following format.

```bash
name                          host                          user
------------------------------------------------------------------------------------------
host1                         192.168.9.188                 user1
host2                         192.168.9.155                 user2
host3                         192.168.9.156                 user3
test                          192.168.9.157                 user4
```

**`sshm del`**

Delete an account.

```bash
sshm del host1
```

**`sshm update`**

Update an account.

The arguments list is same with `add` command, all the specified fields will be updated.

```bash
# change the host1's host field to domain.com
sshm update host1 -H domain.com

# change the host1's password
sshm update host1 -p

# change the host1's identity to identity2
sshm update host1 -i identity2

# change the host1's name to host2, and the next time you want to 
# change the account you have to use `sshm update host2 ...`
sshm update host1 -n host2
```

**`sshm connect`**

Connect to an account.

```bash
sshm connect host1
```

## Todo

- scp support
- jump host support
- X11Forward support(test)