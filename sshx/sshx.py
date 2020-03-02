# -*- coding: future_fstrings -*-

import sys
import time
import click

from collections import OrderedDict

from . import __version__, logger, set_debug
from . import cfg
from . import utils
from . import sshwrap
from . import const as c
from .sshx_forward import Forwards
from .sshx_scp import TargetPair
from .const import STATUS_SUCCESS, STATUS_FAIL


RETRY = 0
RETRY_INTERVAL = 5


def handle_init(force=False, security=False):
    check = cfg.check_init()

    if check == cfg.STATUS_UNINIT:
        cfg.init_config(security=security)
        logger.info('Initialized.')
        return STATUS_SUCCESS
    elif check == cfg.STATUS_INITED:
        if force:
            cfg.remove_all_config()
            cfg.init_config(security=security)
            logger.info('Force initialized.')
            return STATUS_SUCCESS
        else:
            logger.error(
                "Already initialized. If you want to reinit it, please add --force option. Attention: it will delete all existing config files.")
            return STATUS_FAIL
    elif check == cfg.STATUS_BROKEN:
        cfg.remove_all_config()
        cfg.init_config(security=security)
        logger.info('Re-initialized.')
        return STATUS_SUCCESS


def handle_config(security=None, chphrase=False):
    config = cfg.config

    if security is not None:
        config.set_security(security=security)
        cfg.write_config(config)
        return STATUS_SUCCESS

    if chphrase:
        config.reset_passphrase()
        cfg.write_config(config)
        logger.info('Passphrase changed.')
        return STATUS_SUCCESS

    return STATUS_FAIL


def handle_add(name, host, port=c.DEFAULT_PORT, user=c.DEFAULT_USER, password='', identity='', via=''):
    if via == name:
        logger.error(c.MSG_CONNECT_VIA_SELF)
        return STATUS_FAIL

    config = cfg.config

    if via and not config.get_account(via):
        logger.error(f"Jump account '{via}' doesn't exist.")
        return STATUS_FAIL

    if config.get_account(name):
        logger.error('Account exists!')
        return STATUS_FAIL

    passphrase = ''
    if identity:
        if not utils.sshkey_exists(identity):
            logger.error('Identity file not found!')
            return STATUS_FAIL

        # set identity passphrase
        if utils.sshkey_has_passphrase(identity):
            passphrase = utils.read_passphrase()

    account = cfg.Account(
        name=name, host=host, port=port, via=via, passphrase=passphrase,
        user=user, password=password, identity=identity,
    )
    if config.add_account(account):
        cfg.write_config(config)
        logger.info('Account added.')
        return STATUS_SUCCESS
    else:
        return STATUS_FAIL


def handle_update(name, update_fields):
    config = cfg.config

    if not update_fields:
        logger.error('Nothing to update')
        return STATUS_FAIL

    # need to decrypt when updating sensitive data
    _sensitive = ['password', 'identity']
    decrypt = any([f in update_fields for f in _sensitive])

    account = config.get_account(name, decrypt=decrypt)
    if not account:
        logger.error(c.MSG_ACCOUNT_NOT_FOUND)
        return STATUS_FAIL

    # rename
    newname = update_fields.pop('name', None)
    if newname:
        if config.rename_account(account, newname):
            logger.info(f"Account {name} was renamed to {newname}.")
        else:
            logger.info(f"Failed to rename '{name}' to '{newname}'")
            return STATUS_FAIL

    # update via
    via = update_fields.get('via', None)
    if via:
        if name == via:
            logger.error(c.MSG_CONNECT_VIA_SELF)
            return STATUS_FAIL

        if not config.get_account(via):
            logger.error(f"Jump account '{via}' doesn't exist.")
            return STATUS_FAIL

    # need to update passphrase when updating identity
    identity = update_fields.get('identity', None)
    if identity:
        if not utils.sshkey_exists(identity):
            logger.error('Identity file not found!')
            return STATUS_FAIL

        # set identity passphrase
        if utils.sshkey_has_passphrase(identity):
            if not utils.sshkey_check_passphrase(identity, account.passphrase):
                update_fields['passphrase'] = utils.read_passphrase()
        else:
            update_fields['passphrase'] = ''
    elif identity == '':
        # unset identity
        update_fields['passphrase'] = ''
        if not account.password and not 'password' in update_fields:
            logger.info(
                f'Identity was unset but no password was set, please set an password for account {account.name}')
            update_fields['password'] = utils.read_password()

    account.update(update_fields)
    cfg.write_config(config)
    logger.info('Account updated.')
    return STATUS_SUCCESS


def handle_del(name):
    config = cfg.config

    if not config.remove_account(name):
        logger.error(f'Failed to delete.')
        return STATUS_FAIL

    cfg.write_config(config)
    logger.info('Acccount deleted.')
    return STATUS_SUCCESS


def handle_list(key='name', reverse=False):
    config = cfg.config

    accounts = config.get_accounts()

    print('%-20s%-30s%-20s%-20s' % ('name', 'host', 'user', 'via'))
    print('%-20s%-30s%-20s%-20s' % ('-----', '-----', '-----', '-----'))
    accounts.sort(key=lambda a: str.lower(getattr(a, key)), reverse=reverse)
    for a in accounts:
        print('%-20s%-30s%-20s%-20s' % (a.name, a.host, a.user, a.via))
    return STATUS_SUCCESS


def handle_show(name, password=False):
    config = cfg.config

    account = config.get_account(name, decrypt=password)
    if not account:
        logger.error(c.MSG_ACCOUNT_NOT_FOUND)
        return STATUS_FAIL

    if not password:
        del account.password

    print(account)
    return STATUS_SUCCESS


def handle_connect(name, via='', forwards=None, extras='', detach=False,
                   tty=True, background=False, execute=True, cmd=''):
    config = cfg.config

    account = config.get_account(name, decrypt=True)
    if not account:
        logger.error(c.MSG_ACCOUNT_NOT_FOUND)
        return STATUS_FAIL

    via = via or account.via

    return sshwrap.ssh(
        account, vias=via, forwards=forwards, extras=extras, detach=detach,
        tty=tty, background=background, execute=execute, cmd=cmd,
        retry=RETRY, retry_interval=RETRY_INTERVAL)


def handle_forward(name, maps=None, rmaps=None, via='', background=False):
    forwards = Forwards(maps, rmaps)

    return handle_connect(name, via=via, forwards=forwards, detach=background,
                          tty=False, background=background, execute=False)


def handle_socks(name, via='', bind=1080, background=False):
    # -D 1080           dynamic forwarding
    # -fNT -D 1080      ssh socks
    extras = f'-D {bind}'
    return handle_connect(name, via=via, extras=extras, detach=background,
                          tty=False, background=background, execute=False)


def handle_exec(name, via='', tty=False, cmd=[]):
    _cmd = ' '.join(cmd)
    extras = '-t' if tty else ''
    return handle_connect(name, via=via, extras=extras, cmd=_cmd)


def handle_scp(src, dst, via='', with_forward=False):
    targets = TargetPair(src, dst)

    if targets.both_are_remote():
        # TODO: implement copy between remote targets
        logger.error('Copy between remote targets are not supported yet.')
        return STATUS_FAIL

    config = cfg.config

    name = targets.src.host or targets.dst.host
    account = config.get_account(name, decrypt=True)

    if not account:
        logger.error('Account not found')
        return STATUS_FAIL

    return sshwrap.scp(account, targets, vias=via, with_forward=with_forward)


def handle_copyid(name, identity, via=''):
    config = cfg.config
    account = config.get_account(name, decrypt=True)
    ret = sshwrap.ssh_copy_id(account, identity, vias=via)
    if ret == STATUS_SUCCESS:
        logger.info('Succeeded')
    else:
        logger.error('Failed')
    return ret


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
@click.option('--forever', is_flag=True, help='Keep ssh connection forever.')
@click.option('--retry', type=RETRY_TYPE, default=0,
              help='Reconnect after connection closed, repeat for retry times. Supported values are "always" or non negative integer. If retry was enabled, --interval must be greater than 0.')
@click.option('--retry-interval', type=click.IntRange(min=0), default=5,
              help='Sleep seconds before every retry.')
def cli(debug, interval, countmax, forever, retry, retry_interval):
    set_debug(debug)

    global RETRY, RETRY_INTERVAL
    RETRY = retry
    RETRY_INTERVAL = retry_interval

    sshwrap.ServerAliveInterval = interval
    sshwrap.ServerAliveCountMax = countmax

    if forever:
        # Set the alive time to 100 years, forever of life. :)
        # More likely, the connection would be closed by network issue.
        sshwrap.ServerAliveInterval = 60
        sshwrap.ServerAliveCountMax = 60 * 24 * 365 * 100


@cli.command('init', help='Initialize the account storage.')
@click.option('-f', '--force', is_flag=True,
              help=f'Delete previous existing files in {cfg.CONFIG_DIR} and re-init.')
@click.option('--security', is_flag=True, help='Enable security mode.')
def command_init(force, security):
    return handle_init(force=force, security=security)


@cli.command('config', help='Security configuration.')
@click.option('--security-on', 'security', flag_value=True, default=None, help='Enable security mode.')
@click.option('--security-off', 'security', flag_value=False, default=None, help='Disable security mode.')
@click.option('--chphrase', is_flag=True, help='Change the passphrase.')
def command_config(security, chphrase):
    return handle_config(security=security, chphrase=chphrase)


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
        user, host, port = utils.parse_user_host_port(l)

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
@click.option('-e', '--extras', default='', help='Extra arguments for ssh.')
def command_connect(name, via, extras):
    return handle_connect(name, via=via, extras=extras)


@cli.command('forward', help='SSH port forward via specified account.')
@click.argument('name')
@click.option('-v', '--via', help='Account name of jump host.')
@click.option('-L', '-f', '--forward', multiple=True,
              help='[bind_address]:<bind_port>:<remote_address>:<remote_port> => Forward local bind_address:bind_port to remote_address:remote_port.')
@click.option('-R', '-rf', '--rforward', multiple=True,
              help='<bind_address>:<bind_port>:<local_address>:<local_port> => Forward remote bind_address:bind_port to local local_address:local_port.')
@click.option('-b', '--background', is_flag=True,
              help='Run in background.')
def command_forward(name, via, forward, rforward, background):
    if forward or rforward:
        return handle_forward(name, via=via, maps=forward, rmaps=rforward, background=background)
    logger.error('Either -f or -rf option must be specified.')
    return STATUS_FAIL


@cli.command('socks', help='Establish a socks5 server using ssh.')
@click.argument('name')
@click.option('-p', '--port', type=click.IntRange(min=1, max=65535), help='Alias of --bind 127.0.0.1:<port>. (Deprecated)')
@click.option('--bind', help='Bind address like [host:]<port>.', default='127.0.0.1:1080')
@click.option('-v', '--via')
@click.option('-b', '--background', is_flag=True, help='Run in background.')
def command_socks(name, port, bind, via, background):
    bind = port or bind
    return handle_socks(name, via=via, bind=bind, background=background)


@cli.command('scp', help='Copy files with specified accounts.')
@click.argument('src')
@click.argument('dst')
@click.option('-v', '--via')
def command_scp(src, dst, via):
    return handle_scp(src, dst, via=via)


@cli.command('scp2', help='Copy files with specified accounts. This can be used for scp without ProxyJump option support.')
@click.argument('src')
@click.argument('dst')
@click.option('-v', '--via')
def command_scp2(src, dst, via):
    return handle_scp(src, dst, via=via, with_forward=True)


@cli.command('exec', help='Execute a command on the remote host.')
@click.argument('name')
@click.argument('cmd', required=True, nargs=-1)
@click.option('-v', '--via')
@click.option('--tty', is_flag=True)
def command_exec(name, cmd, via, tty):
    return handle_exec(name, via=via, tty=tty, cmd=cmd)


@cli.command('copyid', help='Copy ssh publickey (*.pub) to remote host.')
@click.argument('identity')
@click.argument('name')
@click.option('-v', '--via', help='Jump hosts.')
def command_copyid(identity, name, via):
    return handle_copyid(name, identity, via=via)


@cli.resultcallback()
def process_result(result, debug, interval, countmax, forever, retry, retry_interval):
    '''The result is used as the exit status code.'''
    return result


def invoke(argv):
    try:
        return cli(args=argv, standalone_mode=False)
    except Exception as e:
        logger.error(e)
        return STATUS_FAIL


def main():
    return invoke(sys.argv[1:])


if __name__ == '__main__':
    sys.exit(main())
