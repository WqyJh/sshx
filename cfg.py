import os
import stat
import json
import shutil

from account import *

HOME = os.environ['USERPROFILE'] if os.name == 'nt' else os.environ['HOME']

_CONFIG_DIR = '.sshm'
_ACCOUNT_FILE = '.accounts'

CONFIG_DIR = ''
ACCOUNT_FILE = ''


def set_home(home):
    global HOME
    global CONFIG_DIR
    global ACCOUNT_FILE

    HOME = home
    CONFIG_DIR = os.path.join(HOME, _CONFIG_DIR)
    ACCOUNT_FILE = os.path.join(CONFIG_DIR, _ACCOUNT_FILE)


set_home(HOME)

STATUS_INITED = 0
STATUS_BROKEN = 1
STATUS_UNINIT = 2

_fields = ['name', 'host', 'port', 'user', 'password', 'identity']


def _validate_account_config(account):
    if account:
        for f in _fields:
            if not isinstance(account.get(f, None), str):
                return False
        return True
    return False


def validate_config(config):
    if config:
        lazy = config.get('lazy', None)
        phrase = config.get('phrase', None)
        accounts = config.get('accounts', None)

        if lazy:
            flag = isinstance(lazy, bool) and isinstance(
                phrase, str) and isinstance(accounts, list)
        else:
            flag = isinstance(lazy, bool) and isinstance(accounts, list)

        if flag:
            for account in accounts:
                if not _validate_account_config(account):
                    return False
            return True
    return False


def create_config_file():
    open(ACCOUNT_FILE, 'a').close()
    os.chmod(ACCOUNT_FILE, stat.S_IRUSR | stat.S_IWUSR)


def read_config():
    with open(ACCOUNT_FILE, 'r', encoding='utf-8') as configfile:
        config = json.load(configfile)
        if validate_config(config):
            return config, config['accounts']
    return (None, None)


def write_config(config):
    with open(ACCOUNT_FILE, 'w', encoding='utf-8') as configfile:
        json.dump(config, configfile)


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
        return find_by_name(aclist, name)


def write_account(account):
    config, aclist = read_config()
    if config:
        add_or_update(aclist, account)
        write_config(config)
        return True
    return False


def accounts_num():
    config, aclist = read_config()
    if config:
        return len(aclist)
    return 0
