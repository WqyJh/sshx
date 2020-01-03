import os
import re
import sys
import time
import click

from collections import OrderedDict
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
    config.accounts.sort(key=lambda a: str.lower(
        getattr(a, key)), reverse=reverse)
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


class RetryType(click.ParamType):
    name = "retry"

    def convert(self, value, param, ctx):
        try:
            if value == 'always':
                return 'always'

            v = int(value)
            if v >= 0:
                return v
        except ValueError:
            pass

        self.fail(f'{value} is invalid', param, ctx)


RETRY_TYPE = RetryType()


class SortedGroup(click.Group):
    '''Thanks to https://github.com/pallets/click/issues/513#issuecomment-301046782.'''
    def __init__(self, name=None, commands=None, **attrs):
        if commands is None:
            commands = OrderedDict()
        elif not isinstance(commands, OrderedDict):
            commands = OrderedDict()
        click.Group.__init__(self, name=name, commands=commands, **attrs)

    def list_commands(self, ctx):
        return self.commands.keys()


@click.group(cls=SortedGroup)
@click.version_option(__version__)
@click.option('-d', '--debug', is_flag=True)
@click.option('--interval', type=click.IntRange(min=0), default=0,
              help='ServerAliveInterval for ssh_config.')
@click.option('--countmax', type=click.IntRange(min=0), default=3,
              help='ServerAliveCountMax for ssh_config.')
@click.option('--retry', type=RETRY_TYPE, default=0,
              help='Reconnect after connection closed, repeat for retry times. Supported values are "always" or non negative integer. If retry was enabled, --interval must be greater than 0.')
@click.option('--retry-interval', type=click.IntRange(min=0), default=0,
              help='Sleep seconds before every retry.')
def cli(debug, interval, countmax, retry, retry_interval):
    set_debug(debug)

    global RETRY, RETRY_INTERVAL
    RETRY = retry
    RETRY_INTERVAL = retry_interval

    sshwrap.ServerAliveInterval = interval
    sshwrap.ServerAliveCountMax = countmax


@cli.command('init', help='Initialize the account storage.')
@click.option('-f', '--force', is_flag=True,
              help=f'Delete previous existing files in {cfg.CONFIG_DIR} and re-init.')
def command_init(force):
    return handle_init(force=force)


@cli.command('add', help='Add an account and assign a name for it.')
@click.argument('name')
@click.option('-l', help='<user>@<host>[:port]')
@click.option('-H', '--host', default=c.DEFAULT_HOST)
@click.option('-P', '--port', default=c.DEFAULT_PORT)
@click.option('-u', '--user', default=c.DEFAULT_USER)
@click.option('-p', '--password', is_flag=True)
@click.option('-i', '--identity', default='', help='SSH identity file.')
@click.option('-v', '--via', default='', help='Account name of jump host.')
def command_add(name, l, host, port, user, password, identity, via):
    password = utils.read_password() if password or not identity else ''
    if l:
        user, host, port = parse_user_host_port(l)

    return handle_add(name, host, port=port, user=user, password=password,
                      identity=identity, via=via)


@cli.command('update', help='Uupdate an specified account.')
@click.argument('name')
@click.option('-n', '--rename', help='New name.')
@click.option('-H', '--host')
@click.option('-P', '--port')
@click.option('-u', '--user')
@click.option('-p', '--password', is_flag=True)
@click.option('-i', '--identity')
@click.option('-v', '--via')
def command_update(name, rename, host, port, user, password, identity, via):
    d = {}
    if rename is not None:
        d['name'] = rename
    if host is not None:
        d['host'] = host
    if port is not None:
        d['port'] = port
    if user is not None:
        d['user'] = user
    if password:
        d['password'] = utils.read_password()
    if identity is not None:
        d['identity'] = identity
    if via is not None:
        d['via'] = via

    return handle_update(name, update_fields=d)


@cli.command('del', help='Delete an account.')
@click.argument('name')
def command_del(name):
    return handle_del(name)


@cli.command('list', help='List all accounts.')
@click.option('--sort', type=click.Choice(['name', 'host', 'user']),
              default='name', help='Sort by keys.')
@click.option('--reverse', is_flag=True)
def command_list(sort, reverse):
    return handle_list(key=sort, reverse=reverse)


@cli.command('show', help='Show account info.')
@click.argument('name')
@click.option('-p', '--password', is_flag=True)
def command_show(name, password):
    return handle_show(name, password=password)


@cli.command('connect', help='Connect with specified account.')
@click.argument('name')
@click.option('-v', '--via', help='Account name of jump host.')
def command_connect(name, via):
    return handle_connect(name, via=via)


@cli.command('forward', help='SSH port forward via specified account.')
@click.argument('name')
@click.option('-v', '--via', help='Account name of jump host.')
@click.option('-f', '--forward', multiple=True,
              help='[bind_address]:<bind_port>:<remote_address>:<remote_port> => Forward local bind_address:bind_port to remote_address:remote_port.')
@click.option('-rf', '--rforward', multiple=True,
              help='<bind_address>:<bind_port>:<local_address>:<local_port> => Forward remote bind_address:bind_port to local local_address:local_port.')
@click.option('-b', '--background', is_flag=True,
              help='Run in background.')
def command_forward(name, via, forward, rforward, background):
    return handle_forward(name, via=via, maps=forward, rmaps=rforward, background=background)


@cli.command('socks', help='Establish a socks5 server using ssh.')
@click.argument('name')
@click.option('-p', '--port', type=click.IntRange(min=1, max=65535), default=1080)
@click.option('-v', '--via')
@click.option('-b', '--background', is_flag=True, help='Run in background.')
def command_socks(name, port, via, background):
    return handle_socks(name, via=via, port=port, background=background)


@cli.command('scp', help='Copy files with specified accounts.')
@click.argument('src')
@click.argument('dst')
@click.option('-v', '--via')
def command_scp(src, dst, via):
    return handle_scp(src, dst, via=via)


@cli.command('exec', help='Execute a command on the remote host.')
@click.argument('name')
@click.argument('cmd', required=True, nargs=-1)
@click.option('-v', '--via')
@click.option('--tty', is_flag=True)
def command_exec(name, cmd, via, tty):
    return handle_exec(name, via=via, tty=tty, exec=cmd)


@cli.resultcallback()
def process_result(result, debug, interval, countmax, retry, retry_interval):
    if result:
        logger.info('[%s]: %s' % (result['status'], result['msg']))


def invoke(argv):
    return cli(argv, standalone_mode=False)


def main():
    cli(args=sys.argv[1:])


if __name__ == '__main__':
    main()
