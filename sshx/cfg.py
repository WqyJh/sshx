# -*- coding: future_fstrings -*-

import os
import io
import stat
import shutil
import lazy_object_proxy as lazy

from typing import List

from sshx import logger

from .account import *

from . import utils
from . import tokenizer
from . import const as c


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
    def __init__(self, config_dict, load=True):
        '''
        Construct from dict.

        Use __dict__ to convert to dict.

        __init__() and __dict__ are reciprocal.
        '''
        self.security = config_dict.get('security', False)
        self.phrase = config_dict.get('phrase', None)
        self._phrase = None  # security passphrase or None
        self.accounts = [Account(**a) for a in config_dict.get('accounts', [])]
        # self._load = load
        self.encrypted = {a.name: load for a in self.accounts}

    def is_valid(self):
        b = utils.is_str(self.phrase) and isinstance(
            self.accounts, list) and all(map(Account.is_valid, self.accounts))
        return b

    def dump(self):
        return {
            'security': self.security,
            'phrase': self.phrase,
            'accounts': self.accounts,
        }

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def get_passphrase(self) -> str:
        if self.security:
            if self._phrase is None:
                _phrase = utils.read_passphrase()
                if self.verify_passphrase(_phrase):
                    self._phrase = _phrase
            return self._phrase
        else:
            return self.phrase

    def reset_passphrase(self):
        '''Can't be called until all accounts was decrypted.'''
        if self.security:
            self._phrase = utils.read_passphrase()
            self.phrase = tokenizer.hash(self._phrase)
        else:
            self._phrase = None
            self.phrase = utils.random_str(32)

    def verify_passphrase(self, phrase) -> bool:
        if self.security:
            return self.phrase == tokenizer.hash(phrase)
        return self.phrase == phrase

    def set_security(self, security: bool):
        if self.security:
            if security:
                logger.error('Already in security mode.')
            else:
                self.decrypt_accounts()
                self.security = False
                self.reset_passphrase()
                logger.info('Security mode disabled.')
        else:
            if security:
                self.decrypt_accounts()
                self.security = True
                self.reset_passphrase()
                logger.info('Security mode enabled.')
            else:
                logger.error('Not in security mode.')

    def is_security(self) -> bool:
        return self.security

    def decrypt_account(self, account):
        phrase = self.get_passphrase()
        if phrase:
            if self.encrypted[account.name]:
                account.password = tokenizer.decrypt(account.password, phrase)
                if account.passphrase:
                    account.passphrase = tokenizer.decrypt(account.passphrase, phrase)
                self.encrypted[account.name] = False

    def decrypt_accounts(self):
        for a in self.accounts:
            self.decrypt_account(a)

    def encrypt_account(self, account):
        phrase = self.get_passphrase()
        if phrase:
            if not self.encrypted[account.name]:
                account.password = tokenizer.encrypt(account.password, phrase)
                if account.passphrase:
                    account.passphrase = tokenizer.encrypt(account.passphrase, phrase)
                self.encrypted[account.name] = True

    def encrypt_accounts(self):
        for a in self.accounts:
            self.encrypt_account(a)

    def get_account(self, name, decrypt=False) -> Account:
        account = find_by_name(self.accounts, name)
        if account:
            if decrypt:
                self.decrypt_account(account)
        return account

    def get_accounts(self, decrypt=False) -> List[Account]:
        if decrypt:
            self.decrypt_accounts()
        return self.accounts

    def add_account(self, account):
        a = find_by_name(self.accounts, account.name)
        if a:
            logger.error('Account exists!')
            return False

        self.accounts.append(account)
        self.encrypted[account.name] = False
        return True

    def rename_account(self, account, newname):
        if self.get_account(newname):
            logger.error(f'Account {newname} exists!')
            return False

        encrypted = self.encrypted.pop(account.name)
        account.name = newname
        self.encrypted[newname] = encrypted
        return True

    def remove_account(self, name):
        a = find_by_name(self.accounts, name)
        if not a:
            logger.error('Account not found.')
            return False

        self.accounts.remove(a)
        del self.encrypted[name]
        return True


def create_config_file():
    io.open(ACCOUNT_FILE, 'a', encoding='utf-8').close()
    os.chmod(ACCOUNT_FILE, stat.S_IRUSR | stat.S_IWUSR)


def read_config():
    with io.open(ACCOUNT_FILE, 'r', encoding='utf-8') as configfile:
        config_dict = utils.json_load(configfile.read())
        config = Config(config_dict)

        if config.is_valid():
            return config


def write_config(config):
    with io.open(ACCOUNT_FILE, 'w', encoding='utf-8') as configfile:
        config.encrypt_accounts()
        s = utils.json_dump(config.dump())
        configfile.write(s)


def check_init():
    flags = os.path.isdir(CONFIG_DIR) and os.path.isfile(ACCOUNT_FILE)

    if flags:
        try:
            config = read_config()
            if config:
                return STATUS_INITED
            else:
                return STATUS_BROKEN
        except Exception as e:
            logger.debug(e)

    return STATUS_UNINIT


def init_config(security=False):
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
    create_config_file()

    _config = Config({
        'security': security,
        'phrase': None,
        'accounts': [],
    }, load=False)

    _config.reset_passphrase()

    write_config(_config)


def remove_all_config():
    shutil.rmtree(CONFIG_DIR)


def get_config():
    try:
        return read_config()
    except Exception as e:
        raise Exception(c.MSG_CONFIG_BROKEN)


config = lazy.Proxy(get_config)
