from __future__ import unicode_literals, print_function

import os
import io
import stat
import shutil

from .account import *

from . import utils
from . import tokenizer


_CONFIG_DIR = '.sshx'
_ACCOUNT_FILE = '.accounts'

CONFIG_DIR = ''
ACCOUNT_FILE = ''

def set_config_dir(config_dir):
    global CONFIG_DIR
    global ACCOUNT_FILE

    CONFIG_DIR = config_dir
    ACCOUNT_FILE = os.path.join(CONFIG_DIR, _ACCOUNT_FILE)

ENV_CONFIG_DIR = 'SSHX_HOME'

if ENV_CONFIG_DIR in os.environ:
    set_config_dir(os.environ[ENV_CONFIG_DIR])
else:
    HOME = os.environ['USERPROFILE'] if os.name == 'nt' else os.environ['HOME']
    set_config_dir(os.path.join(HOME, _CONFIG_DIR))


STATUS_INITED = 0
STATUS_BROKEN = 1
STATUS_UNINIT = 2

_fields = ['name', 'host', 'port', 'user', 'password', 'identity']


def _validate_account_config(account):
    if account:
        for f in _fields:
            if not utils.is_str(account.get(f, None)):
                return False
        return True
    return False


def validate_config(config):
    if config:
        phrase = config.get('phrase', None)
        accounts = config.get('accounts', None)

        flag = utils.is_str(phrase) and isinstance(accounts, list)

        if flag:
            for account in accounts:
                if not _validate_account_config(account):
                    return False
            return True
    return False


def create_config_file():
    io.open(ACCOUNT_FILE, 'a', encoding='utf-8').close()
    os.chmod(ACCOUNT_FILE, stat.S_IRUSR | stat.S_IWUSR)


def read_config():
    try:
        with io.open(ACCOUNT_FILE, 'r', encoding='utf-8') as configfile:
            config = utils.json_load(configfile.read())
            if validate_config(config):
                return config, config['accounts']
    except:
        pass
    return (None, None)


def write_config(config):
    with io.open(ACCOUNT_FILE, 'w', encoding='utf-8') as configfile:
        s = utils.json_dump(config)
        configfile.write(s)


def check_init():
    flags = os.path.isdir(CONFIG_DIR) and os.path.isfile(ACCOUNT_FILE)

    if flags:
        config, _ = read_config()
        if config:
            return STATUS_INITED
        else:
            return STATUS_BROKEN

    return STATUS_UNINIT


def remove_all_config():
    shutil.rmtree(CONFIG_DIR)


def read_account(name):
    config, aclist = read_config()
    if config:
        account = find_by_name(aclist, name)
        if account:
            account['password'] = tokenizer.decrypt(account['password'], config['phrase'])
            return account


def write_account(account):
    config, aclist = read_config()
    if config:
        account['password'] = tokenizer.encrypt(account['password'], config['phrase'])
        add_or_update(aclist, account)
        write_config(config)
        return True
    return False


def accounts_num():
    config, aclist = read_config()
    if config:
        return len(aclist)
    return 0
