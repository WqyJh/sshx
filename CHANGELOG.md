# Changelog

## 0.33.3 (2020-12-25)

#### Fixes

* fix unit tests
* delete temp config file after command was executed
* remove psutil for macOS

Full set of changes: [`0.33.0...0.33.3`](https://github.com/WqyJh/sshx/compare/0.33.0...0.33.3)

## 0.33.0 (2020-07-14)

#### New Features

* enable --forever by default
#### Fixes

* fix crash of decryption with python 3.5
#### Docs

* update CHANGELOG.md

Full set of changes: [`0.32.1...0.33.0`](https://github.com/WqyJh/sshx/compare/0.32.1...0.33.0)

## 0.32.1 (2020-03-04)

#### Fixes

* add  for scp via jump hosts
#### Docs

* update CHANGELOG

Full set of changes: [`0.32.0...0.32.1`](https://github.com/WqyJh/sshx/compare/0.32.0...0.32.1)

## 0.32.0 (2020-03-02)

#### New Features

* add future-fstrings for compatibility of python < 3.6
#### Refactorings

* (forward): replace  with
#### Docs

* update CHANGELOG
* add termux documentation
* fix readthedocs badge links in README.md
#### Others

* switch from unittest to pytest

Full set of changes: [`0.31.0...0.32.0`](https://github.com/WqyJh/sshx/compare/0.31.0...0.32.0)

## 0.31.0 (2020-02-24)

#### New Features

* add --extras for connect command
* add command copyid
* use ssh_config for jump hosts instead of `-J/-oProxyJump`
* add ssh_config for jump connection
#### Fixes

* fix port for account.to_ssh_config()
* add retry for SSHPexpect.run to fix retry with background
* encrypt identity passphrase
* add --bind for command socks to replace -p
#### Docs

* udpate CHANGELOG.md
* fix readthedocs links in README.md
* update README.md to reference to sphinx document
* add sphinx docs
#### Others

* fix readthedocs build
* add bump_version.sh
* fix filemode of private key of test data

Full set of changes: [`0.27.1...0.31.0`](https://github.com/WqyJh/sshx/compare/0.27.1...0.31.0)

## 0.27.1 (2020-02-14)

#### New Features

* add --forever option to keep ssh connection alive forever
* add socks via
* add daemonize for running in background
* add security option
#### Fixes

* set expect() to never timeout for foreground
* fix timeout of forward & socks
* fix scp with jump and add tests
* fix local variable 'p' referenced before assignment
#### Refactorings

* update the sshwrap to oop style
* update FunctionalTest.test_connect
* use class to encapsulate the configuration
#### Docs

* update CHANGELOG.md & README.md
#### Others

* update .travis.yml

Full set of changes: [`0.23.1...0.27.1`](https://github.com/WqyJh/sshx/compare/0.23.1...0.27.1)

## 0.23.1 (2020-01-06)

#### Fixes

* fix password echo when network is bad
#### Docs

* update CHANGELOG.md

Full set of changes: [`0.23.0...0.23.1`](https://github.com/WqyJh/sshx/compare/0.23.0...0.23.1)

## 0.23.0 (2020-01-03)

#### New Features

* add order for click commands
* add click cli
#### Fixes

* fix tests
* fix expecting and interact
* fix password revealing when reconnecting failed
#### Refactorings

* remove redundant code
#### Docs

* update CHANGELOG.md
* update help
#### Others

* remove osx & fix pipenv python version
* remove legacy .travis/

Full set of changes: [`0.21.9...0.23.0`](https://github.com/WqyJh/sshx/compare/0.21.9...0.23.0)

## 0.21.9 (2019-11-26)

#### New Features

* add keep alive & retry config
* add -b/--background for forward & socks command
#### Fixes

* handle_update
#### Docs

* update CHANGELOG
* add global config & remove some windows stuff

Full set of changes: [`0.19.8...0.21.9`](https://github.com/WqyJh/sshx/compare/0.19.8...0.21.9)

## 0.19.8 (2019-10-09)

#### New Features

* add sort and reverse for command list
* add command exec
#### Fixes

* (update): fix rename account
* fix find_vias
* fix update error
#### Refactorings

* remove interact for exec
* remove win cmd support
#### Docs

* update CHANGELOG.md
* update README.md for command exec
#### Others

* fix travis install script
* use pipenv to replace pip
* set only test in osx for master branch

Full set of changes: [`0.17.5...0.19.8`](https://github.com/WqyJh/sshx/compare/0.17.5...0.19.8)

## 0.17.5 (2019-09-21)

#### New Features

* add socks command
* add debug switch
* add command show
#### Fixes

* fix unittest
* fix uploading failure on OSX
#### Refactorings

* deprecate ssh_pexpect()
* merge the interact and non interact version of ssh_pexpect
#### Docs

* update CHANGELOG.md
* update README.md
* update README.md
#### Others

* remove python < 3.6

Full set of changes: [`0.4.3...0.17.5`](https://github.com/WqyJh/sshx/compare/0.4.3...0.17.5)

## 0.4.3 (2019-07-14)

#### New Features

* remove python 2 support
#### Others

* remove python 3.7 from travis ci
* remote auto-changelog
* add auto-changelog

Full set of changes: [`0.3.1...0.4.3`](https://github.com/WqyJh/sshx/compare/0.3.1...0.4.3)

## 0.3.1 (2019-07-13)

#### New Features

* add logging
#### Fixes

* remove prints
#### Others

* add auto deployment to PYPI

Full set of changes: [`0.3.0...0.3.1`](https://github.com/WqyJh/sshx/compare/0.3.0...0.3.1)

## 0.3.0 (2019-07-12)

#### New Features

* add scp via multiple jump hosts
* add connect via multiple jump hosts
* add jump host for scp
* add scp command
* forward without a shell
* add sshx forward command
#### Fixes

* fix tests.test_connect

Full set of changes: [`0.2.1...0.3.0`](https://github.com/WqyJh/sshx/compare/0.2.1...0.3.0)

## 0.2.1 (2019-06-23)

#### New Features

* add via argument for connect

Full set of changes: [`0.2.0...0.2.1`](https://github.com/WqyJh/sshx/compare/0.2.0...0.2.1)

## 0.2.0 (2019-06-23)

#### New Features

* add jump host in command line
* add jump connection for pexpect
#### Fixes

* fix jump connection error
#### Refactorings

* change some function names
* Use Account in sshwrap
* Encapsulate the config and account into class
#### Others

* Restrict travis building branches

Full set of changes: [`0.1.0...0.2.0`](https://github.com/WqyJh/sshx/compare/0.1.0...0.2.0)

## 0.1.0 (2018-10-18)

#### New Features

* Add test for add command's abbreviation
* Add abbrev syntax for add command
* Add auto-adjust window size
