# sshm (SSH with account managing)

[![Build Status](https://travis-ci.org/WqyJh/sshm.svg?branch=master)](https://travis-ci.org/WqyJh/sshm)
[![codecov](https://codecov.io/gh/WqyJh/sshm/branch/master/graph/badge.svg)](https://codecov.io/gh/WqyJh/sshm)
[![license](https://img.shields.io/badge/LICENCE-GPLv3-brightgreen.svg)](https://raw.githubusercontent.com/WqyJh/sshm/master/LICENSE)


sshm is a lightweight ssh client with account managing. You can assign names to your accounts and connect with the name, without input the username, host, port, password, identity, which is just a waste of time.

## Usage

```bash
sshm init # Create the account storage the first time you use it.

# add an account
sshm add -n name -H domain.com -p 2222 -u username -P password -i identity

# list all accounts
sshm list 

# delete an account
sshm del name

# update an account
sshm update name

# connect an account
sshm connect name
```