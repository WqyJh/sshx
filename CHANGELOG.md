# Changelog

## 0.23.1 (2020-01-06)

#### Fixes

* fix password echo when network is bad

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

## 0.21.9 (2019-11-26)

#### New Features

* add keep alive & retry config
* add -b/--background for forward & socks command
#### Fixes

* handle_update
#### Docs

* update CHANGELOG
* add global config & remove some windows stuff

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

## 0.4.3 (2019-07-14)

#### New Features

* remove python 2 support
#### Others

* remove python 3.7 from travis ci
* remote auto-changelog
* add auto-changelog

## 0.3.1 (2019-07-13)

#### New Features

* add logging
#### Fixes

* remove prints
#### Others

* add auto deployment to PYPI

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

## 0.2.1 (2019-06-23)

#### New Features

* add via argument for connect

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

## 0.1.0 (2018-10-18)

#### New Features

* Add test for add command's abbreviation
* Add abbrev syntax for add command
* Add auto-adjust window size
