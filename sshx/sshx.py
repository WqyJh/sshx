import os
import re
import sys
import time
import argparse

from sshx import logger
from sshx import set_debug

from . import __version__
from . import cfg
from . import utils
from . import sshwrap
from . import const as c
from .sshx_forward import Forwards
from .sshx_scp import TargetPair

MSG_CONFIG_BROKEN = {
    'status': 'fail',
    'msg': 'Fatal, configuration file was broken!',
}

MSG_CONFIG_NOT_FOUND = {
    'status': 'fail',
    'msg': 'Account not found!',
}


RETRY = 0
RETRY_INTERVAL = 0


def perform_init():
    os.makedirs(cfg.CONFIG_DIR, mode=0o700, exist_ok=True)
    cfg.create_config_file()

    phrase = utils.random_str(32)

    config = cfg.Config({
        'phrase': phrase,
        'accounts': [],
    })
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


def handle_add(name, host, port=c.DEFAULT_PORT, user=c.DEFAULT_USER, password='', identity='', via=''):
    if via == name:
        return {
            'status': 'fail',
            'msg': 'Cannot connect via itself.'
        }

    if via and not cfg.read_account(via):
        return {
            'status': 'fail',
            'msg': "Account '%s' doesn't exist." % via,
        }

    if cfg.write_account(cfg.Account(
        name=name, host=host, port=port, via=via,
        user=user, password=password, identity=identity,
    )):
        return {
            'status': 'success',
            'msg': 'Account added.',
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

    if 'via' in update_fields:
        via = update_fields['via']
        if via == name:
            return {
                'status': 'fail',
                'msg': 'Cannot connect via itself.'
            }

        if not cfg.read_account(via):
            return {
                'status': 'fail',
                'msg': "Account '%s' doesn't exist." % via,
            }

    if 'name' in update_fields and update_fields['name'] != account.name:
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
    config = cfg.read_config()
    if not config:
        return MSG_CONFIG_BROKEN

    account = cfg.find_by_name(config.accounts, name)
    if account:
        config.accounts.remove(account)
        cfg.write_config(config)
        return {
            'status': 'success',
            'msg': 'Account deleted.',
        }
    else:
        return MSG_CONFIG_NOT_FOUND


def handle_list(key='name', reverse=False):
    config = cfg.read_config()
    if not config:
        return MSG_CONFIG_BROKEN

    print('%-20s%-30s%-20s%-20s' % ('name', 'host', 'user', 'via'))
    print('%-20s%-30s%-20s%-20s' % ('-----', '-----', '-----', '-----'))
    config.accounts.sort(key=lambda a: str.lower(getattr(a, key)), reverse=reverse)
    for a in config.accounts:
        print('%-20s%-30s%-20s%-20s' % (a.name, a.host, a.user, a.via))


def handle_show(name, password=False):
    account = cfg.read_account(name)
    if not account:
        return {
            'status': 'fail',
            'msg': 'No account found named by "%s", please check the input.' % name,
        }

    if not password:
        del account.password

    print(account)


def handle_connect(name, via='', forwards=None, interact=True, background=False, extras='', exec=''):
    account = cfg.read_account(name)
    if not account:
        return {
            'status': 'fail',
            'msg': 'No account found named by "%s", please check the input.' % name,
        }

    retry = RETRY

    while True:
        msg = sshwrap.ssh(account, vias=via, forwards=forwards, interact=interact,
                            background=background, extras=extras, exec=exec)
        logger.debug(f'retry: {retry} retry_interval: {RETRY_INTERVAL}s')

        if retry == 0:
            break
        elif retry == 'always':
            time.sleep(RETRY_INTERVAL)
            continue
        elif retry > 0:
            retry -= 1
            time.sleep(RETRY_INTERVAL)
            continue

    return msg


def handle_forward(name, maps=None, rmaps=None, via='', background=False):
    forwards = Forwards(maps, rmaps)

    return handle_connect(name, via=via, forwards=forwards, interact=False, background=background)


def handle_socks(name, via='', port=1080, background=False):
    # -D 1080           dynamic forwarding
    # -fNT -D 1080      ssh socks
    extras = '-D {port}'.format(port=port)
    return handle_connect(name, via=via, interact=False, background=background,  extras=extras)


def handle_exec(name, via='', tty=True, exec=[]):
    _exec = ' '.join(exec)
    extras = '-t' if tty else ''
    return handle_connect(name, via=via, extras=extras, exec=_exec)


def handle_scp(src, dst, via=''):
    targets = TargetPair(src, dst)

    if targets.both_are_remote():
        # TODO
        return {
            'status': 'fail',
            'msg': 'Copy between remote targets are not supported yet.',
        }

    name = targets.src.host or targets.dst.host
    account = cfg.read_account(name)

    if not account:
        return {
            'status': 'fail',
            'msg': 'Account <%s> not found.' % name,
        }

    msg = sshwrap.scp(account, targets, vias=via)

    return msg


class store_retry(argparse.Action):
    def __init__(self, nargs=1, **kwargs):
        super().__init__(nargs=nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        value = values[0]
        v = None

        try:
            if value == 'always':
                v = value
            elif int(value) >= 0:
                v = int(value)
        except ValueError:
            pass

        if v is None:
            raise argparse.ArgumentTypeError(f"'{value}' is invalid")

        setattr(namespace, self.dest, v)


def non_negative_int(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError(f"{value} is an invalid")
    return ivalue


parser = argparse.ArgumentParser(prog='sshx')
# Note:
# version='%(prog)s %s' % __version__ is invalid
# version='%(prog)s %(__version__)s' is invalid, too
parser.add_argument('-v', '--version', action='version',
                    version='%(prog)s ' + __version__)
parser.add_argument('-d', '--debug', action='store_true',
                    help='run in debug mode')
parser.add_argument('--interval', type=int, default=0,
                    help='ServerAliveInterval for ssh_config.')
parser.add_argument('--countmax', type=int, default=3,
                    help='ServerAliveCountMax for ssh_config')
parser.add_argument('--retry', action=store_retry, default=0,
                    help='Reconnect after connection closed, repeat for retry times. Supported values are "always" or non negative integer. If retry was enabled, --interval must be greater than 0.')
parser.add_argument('--retry-interval', type=non_negative_int, default=0,
                    help='Sleep seconds before every retry')


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
parser_add.add_argument('-v', '--via', type=str, default='')


parser_update = subparsers.add_parser('update',
                                      help='update an specified account')
parser_update.add_argument('name', type=str,
                           help='account name')
parser_update.add_argument('-n', '--rename', type=str, default=None, help='new name')
parser_update.add_argument('-H', '--host', type=str, default=None)
parser_update.add_argument('-P', '--port', type=str, default=None)
parser_update.add_argument('-u', '--user', type=str, default=None)
parser_update.add_argument('-p', '--password', action='store_true')
parser_update.add_argument('-i', '--identity', type=str, default=None)
parser_update.add_argument('-v', '--via', type=str, default=None)


parser_del = subparsers.add_parser('del', help='delete an account')
parser_del.add_argument('name', help='delete an account')


parser_list = subparsers.add_parser('list', help='list all account')
parser_list.add_argument('--sort', type=str, choices=['name', 'host', 'user'], default='name',
                        help='sort by keys')
parser_list.add_argument('--reverse', action='store_true', default=False)


parser_show = subparsers.add_parser('show', help='show account info')
parser_show.add_argument('name', type=str)
parser_show.add_argument('-p', '--password', action='store_true')


parser_connect = subparsers.add_parser('connect',
                                       help='connect with specified account')
parser_connect.add_argument('name', type=str)
parser_connect.add_argument('-v', '--via', type=str, default=None)
parser_connect.add_argument(
    '-f', '--forward', type=str, nargs='+', default=None)
parser_connect.add_argument(
    '-rf', '--rforward', type=str, nargs='+', default=None)


parser_forward = subparsers.add_parser('forward',
                                       help='ssh port forward via specified account')
parser_forward.add_argument('name', type=str)
parser_forward.add_argument('-v', '--via', type=str, default=None)
parser_forward.add_argument(
    '-f', '--forward', type=str, nargs='+', default=None)
parser_forward.add_argument(
    '-rf', '--rforward', type=str, nargs='+', default=None)
parser_forward.add_argument('-b', '--background', action='store_true',
                        help='run in background')


parser_socks = subparsers.add_parser('socks',
                                     help='establish a socks5 server using ssh')
parser_socks.add_argument('name', type=str)
parser_socks.add_argument('-p', '--port', type=int, default=1080)
parser_socks.add_argument('-v', '--via', type=str, default=None)
parser_socks.add_argument('-b', '--background', action='store_true',
                        help='run in background')


parser_scp = subparsers.add_parser('scp',
                                   help='scp files with specified account')
parser_scp.add_argument('-v', '--via', type=str, default=None)
parser_scp.add_argument('src', type=str)
parser_scp.add_argument('dst', type=str)


parser_exec = subparsers.add_parser('exec',
                                    help='execute a command on the remote host')
parser_exec.add_argument('name', type=str)
parser_exec.add_argument('cmd', nargs=argparse.REMAINDER)
parser_exec.add_argument('-v', '--via', type=str, default=None)
parser_exec.add_argument('--tty', action='store_true', default=False)


def parse_user_host_port(s):
    '''
    user@host:port -> (user, host, port)
    '''
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

    if args.debug:
        set_debug(True)
        logger.debug('run in debug mode')

    global RETRY, RETRY_INTERVAL
    RETRY = args.retry
    RETRY_INTERVAL = args.retry_interval

    sshwrap.ServerAliveInterval = args.interval
    sshwrap.ServerAliveCountMax = args.countmax

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

        msg = handle_add(args.name, host, port=port, user=user, via=args.via,
                         password=password, identity=args.identity)
    elif args.command == 'update':
        d = args.__dict__
        name = d.pop('name')
        if 'rename' in d:
            d['name'] = d.pop('rename')
        print(d)
        updatable_fields = ['name', 'user', 'host', 'port', 'password', 'identity', 'via']
        d = {k: v for k, v in d.items() if k in updatable_fields and v is not None}

        if args.password:
            d['password'] = utils.read_password()
        else:
            del d['password']

        msg = handle_update(name, update_fields=d)
    elif args.command == 'list':
        msg = handle_list(key=args.sort, reverse=args.reverse)
    elif args.command == 'show':
        msg = handle_show(args.name, password=args.password)
    elif args.command == 'del':
        msg = handle_del(args.name)
    elif args.command == 'connect':
        msg = handle_connect(args.name, via=args.via)
    elif args.command == 'forward':
        msg = handle_forward(args.name, via=args.via, maps=args.forward, rmaps=args.rforward,
                            background=args.background)
    elif args.command == 'socks':
        msg = handle_socks(args.name, via=args.via, port=args.port, background=args.background)
    elif args.command == 'scp':
        msg = handle_scp(args.src, args.dst, via=args.via)
    elif args.command == 'exec':
        msg = handle_exec(args.name, via=args.via, tty=args.tty, exec=args.cmd)

    if msg:
        logger.info('[%s]: %s' % (msg['status'], msg['msg']))


def main():
    invoke(sys.argv[1:])


if __name__ == '__main__':
    main()
