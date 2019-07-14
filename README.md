# sshx (SSH eXtensions)

[![Build Status](https://travis-ci.org/WqyJh/sshx.svg?branch=master)](https://travis-ci.org/WqyJh/sshx)
[![codecov](https://codecov.io/gh/WqyJh/sshx/branch/master/graph/badge.svg)](https://codecov.io/gh/WqyJh/sshx)
[![license](https://img.shields.io/badge/LICENCE-GPLv3-brightgreen.svg)](https://raw.githubusercontent.com/WqyJh/sshx/master/LICENSE)


sshx is a lightweight wrapper for ssh/scp command, which has the following features:
- Remember your ssh account
- Connect to your account with a short command, without typing password
- Enable jump host for your connection
- Create ssh forwarding with a short command, without typing password
- Enable jump host for your port forwarding
- Copy files from/to your account with a short command, without typing password
- Enable jump host for your scp connection


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

pip install -i  https://wqyjh.github.io/python-wheels/ pyHook
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
sshx add myhost -l test@192.168.9.155
```

(This command will ask you to type your password and sshx would store the encrypted password.)

3. Connect to the account.

```bash
sshx connect myhost
```

## Usage

### Initialization

`sshx init` performs initialization.

It will automatically create the following files which storing the account info. If the files are damaged you'll probably 
lost all the account records, so **DON'T TOUCH IT**. If this happened, use this command to re-init and use
`add` command to re-add them.

```bash
$ sshx init
$ tree ~/.sshx
~/.sshx
└── .accounts
```

### Add accounts

`sshx add` adds an account.

```bash
# add an account in an simple way
sshx add myhost -l user@host:port

# add an account and specify an password for authentication
sshx add myhost -H host -P port -u user -p

# add an account and specify an identity file for authentication
sshx add myhost -H host -P port -u user -i identity_file

# add an account and specify both password and identity file for authentication
sshx add myhost -H host -P port -u user -p -i identity_file

# add an account named myhost2 and specify an password for authentication
# use pre-added myhost as it's jump host
sshx add -l user@host:port -v myhost myhost2
```

- Host and user options are required for adding an account.
- Either a password or a identity option is required for adding an account. You can also specify both of them for an account. In this case, only using identity for authentication(maybe improved later).
- Password are input from the prompt, which won't show in the screen.


### Show accounts


`sshx list` lists all the accounts in the following format.

```bash
name                host                          user                via                 
-----               -----                         -----               -----               
host1               192.168.7.1                   root                                    
host2               192.168.7.2                   test                host1               
host3               192.168.7.3                   root                host2               
```

### Delete accounts

`sshx del` deletes an account.

```bash
sshx del host1
```

### Update accounts

`sshx update` updates an account.

The supported options are the same with `add` command, all the specified fields will be updated.

```bash
# change the host1's host field to domain.com
sshx update host1 -H domain.com

# change the host1's password
sshx update host1 -p

# change the host1's identity to identity2
sshx update host1 -i identity2

# TODO
# change the host1's name to host2, and the next time you want to 
# change the account you have to use `sshx update host2 ...`
#sshx update host1 -n host2
```

### Connect accounts

`sshx connect` connect to an account.

```bash
# Connect to host1 directly.
sshx connect host1

# Connect to host1 using host2 as jump host.
# If the host1 was originally has an jump host,
# this argument would temporarily override it.
sshx connect host1 -v host2

# Connect to hsot1 using host2 as jump host,
# while the host2 is using host3 as jump host.
sshx connect host1 -v host2,host3
```

**Note** that if you use `-v` option, all of the accounts' 
via field will be ignored.


### Create port forwardings

`sshx forward` creates port fowardings.

```bash
sshx forward host1 [-f <map1> [map2]] [-rf <rmap1> [rmap2]] [-v host2[,host3]]

map: [bind_address]:bind_port:remote_address:remote_port

rmap: bind_address:bind_port:local_address:local_port
```

For example:

```bash
# Forward localhost:8888 to 192.168.77.7:80, 
# while the host1 is the intermedia server, 
# so you must ensure the host1 could dial to 192.168.77.7:80.
sshx forward host1 -f :8888:192.168.77.7:80
```

```bash
# Forward host1:8888 to 192.168.99.9:8888. 
# When you access localhost:8000 on host1, 
# the connection would be forward to 192.168.99.9:8888, 
# while your computer is working as a intermediate server 
# so you have to ensure your computer has access to 192.168.99.9:8888.
sshx forward host1 -r :8000:192.168.99.9:8888
```

- You can use `-f` and `-rf` arguments simultaneously.
- You can also specify multiple maps after either `-f` or `-rf`.
- You can use `-v` option to specify jump hosts just as connect.


### Copy files

`sshx scp` copy files to/from servers.

```bash
# Copy local files to host1
sshx scp <src> host1:<dst>

# Copy remote files from host1 to local
sshx scp host1:<src> <dst>

# Copy local files to host1, using host2 as jump host
sshx scp <src> host1:<dst> -v host2

# Copy remote files to local, using host2 as jump host
# and using host3 as host2's jump host.
sshx scp host1:<src> <dst> -v host2,host3
```

TODO:
```bash
# Copy remote files from host1 to host2
sshx scp host1:<src> host2:<dst>
```

## Test

```bash
python setup.py test
```

## Todo

- [x] scp support
- [x] jump host support


## Bugs

