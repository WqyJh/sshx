from __future__ import unicode_literals, print_function

import os
import re
import sys
import argparse

from . import __version__
from . import cfg
from . import utils
from . import sshwrap
from . import const as c

MSG_CONFIG_BROKEN = {
    'status': 'fail',
    'msg': 'Fatal, configuration file was broken!',
}

MSG_CONFIG_NOT_FOUND = {
    'status': 'fail',
    'msg': 'Account exists!',
}


def perform_init():
    os.makedirs(cfg.CONFIG_DIR, mode=0o700)
    cfg.create_config_file()

    phrase = utils.random_str(32)

    config = {
        'phrase': phrase,
        'accounts': [],
    }
    cfg.write_config(config)


def handle_init(force=False):
    check = cfg.check_init()
    msg = {
        'status': 'unknown',
        'msg': '',
    }

    if check == cfg.STATUS_UNINIT:
        perform_init()
        msg = {
            'status': 'success',
            'msg': 'Initialized.',
        }
    elif check == cfg.STATUS_INITED:
        if force:
            cfg.remove_all_config()
            perform_init()
            msg = {
                'status': 'success',
                'msg': 'Force initialized.',
            }
        else:
            msg = {
                'status': 'fail',
                'msg': "Already initialized. If you want to reinit it, please add --force option. Attention: it will delete all existing config files.",
            }
    elif check == cfg.STATUS_BROKEN:
        cfg.remove_all_config()
        perform_init()
        msg = {
            'status': 'success',
            'msg': 'Re-initialized.',
        }
    return msg


def handle_add(name, host, port=c.DEFAULT_PORT, user=c.DEFAULT_USER, password='', identity=''):
    if cfg.write_account({
        'name': name,
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'identity': identity,
    }):
        return {
            'status': 'success',
            'msg': 'Account added.'
        }
    else:
        return {
            'status': 'fail',
            'msg': 'Account exists!',
        }


def handle_update(name, update_fields):
    if not update_fields:
        return {
            'status': 'fail',
            'msg': 'Nothing updated.'
        }

    account = cfg.read_account(name)
    if not account:
        return MSG_CONFIG_NOT_FOUND

    if 'name' in update_fields and update_fields['name'] != account['name']:
        handle_del(name)

    account.update(update_fields)
    if cfg.write_account(account):
        return {
            'status': 'success',
            'msg': 'Account updated.',
        }
    else:
        return MSG_CONFIG_BROKEN


def handle_del(name):
    config, aclist = cfg.read_config()
    if not config:
        return MSG_CONFIG_BROKEN

    account = cfg.find_by_name(aclist, name)
    if account:
        aclist.remove(account)
        cfg.write_config(config)
        return {
            'status': 'success',
            'msg': 'Account deleted.',
        }
    else:
        return MSG_CONFIG_NOT_FOUND


def handle_list():
    config, aclist = cfg.read_config()
    if not config:
        return MSG_CONFIG_BROKEN

    print('%-30s%-30s%-30s' % ('name', 'host', 'user'))
    print('-' * 90)
    for a in aclist:
        print('%-30s%-30s%-30s' % (a['name'], a['host'], a['user']))


def handle_connect(name):
    account = cfg.read_account(name)
    if not account:
        return {
            'status': 'fail',
            'msg': 'No account found named by "%s", please check the input.' % name,
        }

    if account['identity']:
        msg = sshwrap.ssh(account['host'], account['port'], account['user'],
                          identity=account['identity'])
    else:
        msg = sshwrap.ssh(account['host'], account['port'], account['user'],
                          password=account['password'])
    return msg


parser = argparse.ArgumentParser(prog='sshx')
# Note:
# version='%(prog)s %s' % __version__ is invalid
# version='%(prog)s %(__version__)s' is invalid, too
parser.add_argument('-v', '--version', action='version',
                    version='%(prog)s ' + __version__)


subparsers = parser.add_subparsers(title='command',
                                   dest='command')


parser_init = subparsers.add_parser('init',
                                    help='initialize the account storage')
parser_init.add_argument('-f', '--force', action='store_true',
                         help='delete previous existing files in %s and re-init' % cfg.CONFIG_DIR)


parser_add = subparsers.add_parser('add',
                                   help='add an account and assign a name for it')
parser_add.add_argument('name', type=str,
                        help='assign an name to this account')
parser_add.add_argument('-l', type=str,
                        help='<user>@<host>[:port]')
parser_add.add_argument('-H', '--host', type=str, default=c.DEFAULT_HOST)
parser_add.add_argument('-P', '--port', type=str, default=c.DEFAULT_PORT)
parser_add.add_argument('-u', '--user', type=str, default=c.DEFAULT_USER)
parser_add.add_argument('-p', '--password', action='store_true', default=True)
parser_add.add_argument('-i', '--identity', type=str, default='')


parser_update = subparsers.add_parser('update',
                                      help='update an specified account')
parser_update.add_argument('name', type=str,
                           help='assign an name to this account')
parser_update.add_argument('-H', '--host', type=str, default=None)
parser_update.add_argument('-P', '--port', type=str, default=None)
parser_update.add_argument('-u', '--user', type=str, default=None)
parser_update.add_argument('-p', '--password', action='store_true')
parser_update.add_argument('-i', '--identity', type=str, default=None)


parser_del = subparsers.add_parser('del', help='delete an account')
parser_del.add_argument('name', help='delete an account')


parser_list = subparsers.add_parser('list', help='list all account')


parser_connect = subparsers.add_parser('connect',
                                       help='connect with specified account')
parser_connect.add_argument('name', type=str)


def parse_user_host_port(s):
    user, host_port = s.split('@')
    splited = host_port.split(':')

    if len(splited) == 2:
        host, port = splited
    else:
        host, port = splited[0], c.DEFAULT_PORT

    return user, host, port


def invoke(argv):
    args = parser.parse_args(argv)

    msg = None

    if not args.command:
        parser.print_help()
    elif args.command == 'init':
        msg = handle_init(force=args.force)
    elif args.command == 'add':
        password = ''
        if args.password:
            password = utils.read_password()

        if args.l:
            user, host, port = parse_user_host_port(args.l)
        else:
            user, host, port = args.user, args.host, args.port

        msg = handle_add(args.name, host, port=port, user=user,
                         password=password, identity=args.identity)
    elif args.command == 'update':
        d = args.__dict__
        name = d.pop('name')
        del d['command']
        d = {k: v for k, v in d.items() if v is not None}

        if args.password:
            d['password'] = utils.read_password()
        else:
            del d['password']

        msg = handle_update(name, update_fields=d)
    elif args.command == 'list':
        msg = handle_list()
    elif args.command == 'del':
        msg = handle_del(args.name)
    elif args.command == 'connect':
        msg = handle_connect(args.name)

    if msg:
        print('[%s]: %s' % (msg['status'], msg['msg']))


def main():
    invoke(sys.argv[1:])


if __name__ == '__main__':
    main()
