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
# add an account in an simpler way
sshx add myhost user@host:port

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

- Host and user option are required for adding an account.
- Either a password or a identity option is required for adding an account. You can also specify both of them for an account. In this case, only using identity for authentication(maybe improved later).
- Password are input from the prompt, which won't show in the screen.

**`sshx list`**

List all the accounts as the following format.

```bash
name                host                          user                via                 
-----               -----                         -----               -----               
host1               192.168.7.1                   root                                    
host2               192.168.7.2                   test                host1               
host3               192.168.7.3                   root                host2               
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

# connect to host1 using host2 as jump host
# If the host1 was originally has an via host,
# this argument would temporarily override it.
sshx connect host1 -v host2

# connect to hsot1 using host2 as jump host,
# while the host2 is using host3 as jump host.
sshx connect host1 -v host2,host3
```

**`sshx forward`**

Forward ports.

```bash
sshx forward host1 [-f <map1> [map2]] [-rf <rmap1> [rmap2]] [-v host2[,host3]]

map: [bind_address]:bind_port:remote_address:remote_port

rmap: bind_address:bind_port:local_address:local_port
```

For example:

```bash
# Forward localhost:8888 to 192.168.77.7:80, while the host1 is the intermedia server, so you must ensure the host1 could dial to 192.168.77.7:80.
sshx forward host1 -f :8888:192.168.77.7:80
```

```bash
# Forward host1:8888 to 192.168.99.9:8888. When you access localhost:8000 on host1, the connection would be forward to 192.168.99.9:8888, while your computer is working as a intermediate server so you have to ensure your computer has access to 192.168.99.9:8888.
sshx forward host1 -r :8000:192.168.99.9:8888
```

You can use `-f` and `-rf` arguments simultaneously.

You can also specify multiple maps after either `-f` or `-rf`.

**`sshx scp`**

Copy files to/from server.

```bash
sshx scp <src> host1:<dst>

sshx scp host1:<src> <dst>

sshx scp <src> host1:<dst> -v host2

sshx scp host1:<src> <dst> -v host2,host3
```

TODO:
```bash
sshx scp host1:<src> host2:<dst>
```

## Test

```bash
python setup.py test
```

## Todo

- [ ] scp support
- [x] jump host support


## Bugs

**1. `python2 setup.py test` failed on every test case related to itsdangerous.**

The traceback looks as follow. Seems the function `want_bytes` was `None`.

```bash
======================================================================
ERROR: test_encrypt_decrypt (sshx.tests.test_tokenizer.TokenizerTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "D:\win-projects\PythonProjects\sshx\sshx\tests\test_tokenizer.py", line 12, in test_encrypt_decrypt
    t = tokenizer.encrypt(s, k)
  File "D:\win-projects\PythonProjects\sshx\sshx\tokenizer.py", line 14, in encrypt
    s = URLSafeSerializer(key)
  File "D:\win-programs\venv\sshxpy2\lib\site-packages\itsdangerous.py", line 518, in __init__
    self.secret_key = want_bytes(secret_key)
TypeError: 'NoneType' object is not callable
```

I don't know what caused it, but it passes all when I run the tests with unittest command

```bash
python -m unittest discover -t ./ -s sshx/tests -v
```

All tests passed with python3.

So I think it's the bug of `setuptools`, and it only affects tests running with python2. Therefore the bug
has nothing to do with the usage but cause the CI failure.