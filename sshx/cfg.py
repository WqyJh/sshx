import os
import io
import stat
import shutil

from sshx import logger

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


class Config(object):
    def __init__(self, config_dict):
        '''
        Construct from dict.

        Use __dict__ to convert to dict.

        __init__() and __dict__ are reciprocal.
        '''
        self.phrase = config_dict.get('phrase', '')
        self.accounts = [Account(**a) for a in config_dict.get('accounts', None)]

    def is_valid(self):
        b = utils.is_str(self.phrase) and isinstance(self.accounts, list) and all(map(Account.is_valid, self.accounts))
        return b

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


def create_config_file():
    io.open(ACCOUNT_FILE, 'a', encoding='utf-8').close()
    os.chmod(ACCOUNT_FILE, stat.S_IRUSR | stat.S_IWUSR)


def read_config():
    try:
        with io.open(ACCOUNT_FILE, 'r', encoding='utf-8') as configfile:
            config_dict = utils.json_load(configfile.read())
            config = Config(config_dict)

            if config.is_valid():
                return config
    except Exception as e:
        logger.critical(e)
    return None


def write_config(config):
    with io.open(ACCOUNT_FILE, 'w', encoding='utf-8') as configfile:
        s = utils.json_dump(config.__dict__)
        configfile.write(s)


def check_init():
    flags = os.path.isdir(CONFIG_DIR) and os.path.isfile(ACCOUNT_FILE)

    if flags:
        config = read_config()
        if config:
            return STATUS_INITED
        else:
            return STATUS_BROKEN

    return STATUS_UNINIT


def remove_all_config():
    shutil.rmtree(CONFIG_DIR)


def read_account(name):
    config = read_config()
    if config:
        account = find_by_name(config.accounts, name)
        if account:
            account.password = tokenizer.decrypt(
                account.password, config.phrase)
            return account


def write_account(account):
    config = read_config()
    if config:
        account.password = tokenizer.encrypt(
            account.password, config.phrase)
        add_or_update(config.accounts, account)
        write_config(config)
        return True
    return False


def accounts_num():
    config = read_config()
    if config:
        return len(config.accounts)
    return 0
