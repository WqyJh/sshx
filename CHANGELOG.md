# Changelog


## 0.27.1
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

## 0.23.1

#### Fixes

* fix password echo when network is bad

## 0.23.0
#### New Features

* add order for click commands
* add click cli

#### Fixes

* fix tests
* fix expecting and interact
* fix password revealing when reconnecting failed

## 0.21.9
#### New Features

* add keep alive & retry config
* add -b/--background for forward & socks command

#### Fixes

* handle_update

## 0.19.8
#### New Features

* add sort and reverse for command list
* add command exec

#### Fixes

* (update): fix rename account
* fix find_vias
* fix update error

## 0.17.5
#### New Features

* add socks command
* add debug switch
* add command show

#### Fixes

* fix unittest
* fix uploading failure on OSX

## 0.4.3
#### New Features

* remove python 2 support


## 0.3.1
#### New Features

* add logging

#### Fixes

* remove prints

## 0.3.0
#### New Features

* add scp via multiple jump hosts
* add connect via multiple jump hosts
* add jump host for scp
* add scp command
* forward without a shell
* add sshx forward command

#### Fixes

* fix tests.test_connect

## 0.2.1
#### New Features

* add via argument for connect


## 0.2.0
#### New Features

* add jump host in command line
* add jump connection for pexpect

#### Fixes

* fix jump connection error

## 0.1.0
#### New Features

* Add test for add command's abbreviation
* Add abbrev syntax for add command
* Add auto-adjust window size

