# -*- coding: future_fstrings -*-

from . import global_test_init
import os
import mock
import shutil
import unittest

import lazy_object_proxy as lazy

from mock import call

from .. import cfg
from .. import sshx
from .. import utils
from .. import sshwrap
from ..const import STATUS_SUCCESS, STATUS_FAIL


BASEDIR = os.path.dirname(__file__)

NOIDENTITY = ''
PUBKEY = 'identity.pub'

NAME1 = 'name1'
HOST1 = 'host1'
PORT1 = 'port1'
USER1 = 'user1'
PASSWORD1 = 'password1'
IDENTITY1 = NOIDENTITY

NAME2 = 'name2'
HOST2 = 'host2'
PORT2 = 'port2'
USER2 = 'user2'
IDENTITY2 = os.path.join(BASEDIR, 'data/rsa1')
PASSWORD2 = 'password2'

NAME3 = 'name3'
HOST3 = 'host3'
PORT3 = 'port3'
USER3 = 'user3'
IDENTITY3 = os.path.join(BASEDIR, 'data/rsa2')
PASSPHRASE3 = '12345678'

PASSWORD3 = 'password3'

NAME4 = 'name4'
HOST4 = 'host4'
PORT4 = 'port4'
USER4 = 'user4'
IDENTITY4 = NOIDENTITY
PASSWORD4 = 'password4'

NAME5 = 'name5'
HOST5 = 'host5'
PORT5 = 'port5'
USER5 = 'user5'
IDENTITY5 = NOIDENTITY
PASSWORD5 = 'password5'

LOCALPORT = 'localport'

DIR1 = 'dir1/'
DIR2 = '/tmp'

FORWARD1 = ':3000:127.0.0.1:3222'
COMMAND1 = 'ls -al'

TEST_DIR = '/tmp/sshx-test-tmp'

_SSH_CONFIG_FILE = 'ssh-config-file'
SSH_CONFIG_FILE = os.path.join(TEST_DIR, _SSH_CONFIG_FILE)


def _reset():
    '''
    Reset the module status.
    Only for unittests.
    '''
    cfg.config = lazy.Proxy(cfg.get_config)


def _patch_sshx_handle(name):
    fn = f'handle_{name}'
    func = getattr(sshx, fn)

    def _wrapped(*args, **kwargs):
        _reset()
        return func(*args, **kwargs)

    setattr(_wrapped, 'original_func', func)
    setattr(sshx, fn, _wrapped)


def _restore_sshx_handle(name):
    fn = f'handle_{name}'
    func = getattr(sshx, fn)

    original_func = getattr(func, 'original_func')
    setattr(sshx, fn, original_func)


def _patch_all_sshx_handle():
    for a in dir(sshx):
        if a.startswith('handle_'):
            name = a.replace('handle_', '')
            _patch_sshx_handle(name)


def _restore_all_sshx_handle():
    for a in dir(sshx):
        if a.startswith('handle_'):
            name = a.replace('handle_', '')
            _restore_sshx_handle(name)


def _setup_config_dir():
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    cfg.set_config_dir(TEST_DIR)


def _teardown_config_dir():
    shutil.rmtree(TEST_DIR, ignore_errors=True)


class InitTest(unittest.TestCase):
    def setUp(self):
        _patch_all_sshx_handle()
        _setup_config_dir()

    def tearDown(self):
        _restore_all_sshx_handle()
        _teardown_config_dir()

    def test_init(self):
        self.assertEqual(cfg.STATUS_UNINIT, cfg.check_init())

        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertTrue(utils.is_str(config.phrase))
        self.assertFalse(config.security)
        self.assertEqual(0, len(config.accounts))
        self.assertIsNotNone(config.get_passphrase())
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())
        phrase = config.phrase

        ret = sshx.handle_init()
        self.assertEqual(STATUS_FAIL, ret)
        config = cfg.read_config()
        self.assertTrue(utils.is_str(config.phrase))
        self.assertFalse(config.security)
        self.assertEqual(0, len(config.accounts))
        self.assertIsNotNone(config.get_passphrase())
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())
        phrase = config.phrase

        ret = sshx.handle_init(force=True)
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertFalse(config.security)
        self.assertEqual(0, len(config.accounts))
        self.assertIsNotNone(config.get_passphrase())
        self.assertNotEqual(phrase, config.phrase)
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        # test security option
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            ret = sshx.handle_init(force=True, security=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m_read_password.assert_called_once()
            m_read_password.reset_mock()
            config = cfg.read_config()
            self.assertTrue(config.security)
            self.assertEqual(0, len(config.accounts))
            self.assertIsNotNone(config.get_passphrase())
            self.assertEqual(PASSWORD1, config._phrase)
            m_read_password.assert_called_once()
            self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

    def test_config(self):
        # Init without security
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m:
            ret = sshx.handle_init()
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_not_called()

            config = cfg.read_config()
            self.assertFalse(config.security)
            self.assertIsNotNone(config.get_passphrase())

        # Enable security option
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m:
            ret = sshx.handle_config(security=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called()

            config = cfg.read_config()
            self.assertIsNotNone(config.get_passphrase())
            self.assertEqual(PASSWORD1, config._phrase)

        # Change passphrase
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m:
            ret = sshx.handle_config(chphrase=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called()

            config = cfg.read_config()
            self.assertTrue(config.security)
            self.assertIsNotNone(config.get_passphrase())
            self.assertEqual(PASSWORD2, config._phrase)

        # Disable security option
        with mock.patch('sshx.utils.random_str', return_value=PASSWORD1) as m:
            ret = sshx.handle_config(security=False)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called_once()

            config = cfg.read_config()
            self.assertFalse(config.security)
            # config.phrase is randomly generate
            self.assertIsNotNone(config.get_passphrase())
            self.assertIsNone(config._phrase)
            self.assertEqual(PASSWORD1, config.phrase)
            m.assert_called_once()
            phrase = config.phrase

        # Change passphrase
        with mock.patch('sshx.utils.random_str', return_value=PASSWORD2) as m:
            ret = sshx.handle_config(chphrase=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called_once()

            config = cfg.read_config()
            self.assertFalse(config.security)
            self.assertIsNotNone(config.get_passphrase())
            self.assertNotEqual(phrase, config.phrase)


class FunctionalTest(unittest.TestCase):
    def setUp(self):
        _patch_all_sshx_handle()
        _setup_config_dir()

        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)

    def tearDown(self):
        _restore_all_sshx_handle()
        _teardown_config_dir()

    def test_add(self):
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))

        acc = config.get_account(NAME1, decrypt=True)
        self.assertEqual(HOST1, acc.host)
        self.assertEqual(PORT1, acc.port)
        self.assertEqual(USER1, acc.user)
        self.assertEqual(PASSWORD1, acc.password)
        self.assertEqual(NOIDENTITY, acc.identity)

        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertEqual(2, len(config.accounts))

    def test_add_identity(self):
        ret = sshx.handle_add(NAME2, HOST2, port=PORT2, user=USER2,
                              password=PASSWORD2, identity=IDENTITY2)
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))

        with mock.patch('sshx.utils.read_passphrase', return_value=PASSPHRASE3) as m:
            ret = sshx.handle_add(NAME3, HOST3, port=PORT3, user=USER3,
                                  password=PASSWORD3, identity=IDENTITY3)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called_once()
            config = cfg.read_config()
            self.assertEqual(2, len(config.accounts))

    def test_add_via(self):
        ret = sshx.handle_init()

        ret = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_FAIL, ret)

        ret = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME2,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_FAIL, ret)

        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        ret = sshx.handle_add(NAME2, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

    def test_update(self):
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        ret = sshx.handle_update(NAME1, update_fields={
            'identity': IDENTITY2,
            'password': PASSWORD2,
        })
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))
        account = config.get_account(NAME1, decrypt=True)
        self.assertEqual(IDENTITY2, account.identity)
        self.assertEqual(PASSWORD2, account.password)

        ret = sshx.handle_update(NAME2, update_fields={
            'identity': IDENTITY2,
        })
        self.assertEqual(STATUS_FAIL, ret)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))

        ret = sshx.handle_update(NAME1, update_fields={
            'name': NAME2,
        })
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))
        account = config.get_account(NAME1)
        self.assertIsNone(account)
        account = config.get_account(NAME2)
        self.assertEqual(IDENTITY2, account.identity)

    def test_del(self):
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        config = cfg.read_config()
        self.assertEqual(2, len(config.accounts))

        sshx.handle_del(NAME1)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))
        self.assertIsNone(cfg.find_by_name(config.accounts, NAME1))

        sshx.handle_del(NAME2)
        config = cfg.read_config()
        self.assertEqual(0, len(config.accounts))
        self.assertIsNone(cfg.find_by_name(config.accounts, NAME2))


def _assert_called_with(m, command):
    m.assert_called_with(utils.format_command(command))


def _assert_called_with_n(self, m, commands):
    calls = m.call_args_list
    self.assertEqual(len(calls), len(commands))
    for c, command in zip(m.call_args_list, commands):
        self.assertEqual(c, call(utils.format_command(command)))


def _assert_file_contains(self, file, token):
    with open(file, 'r') as f:
        if type(token) == str:
            self.assertTrue(token in f.read())
        else:
            content = f.read()
            self.assertTrue(all([t in content for t in token]))


class SpawnCommandTest(unittest.TestCase):
    def setUp(self):
        _patch_all_sshx_handle()
        _setup_config_dir()

        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)

        # Account NAME1
        ret = sshx.handle_add(NAME1, HOST1,
                              port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)

        # Account NAME2
        ret = sshx.handle_add(NAME2, HOST2,
                              port=PORT2,
                              user=USER2, password=PASSWORD2, identity=IDENTITY2)
        self.assertEqual(STATUS_SUCCESS, ret)

        # Account NAME3
        with mock.patch('sshx.utils.read_passphrase', return_value=PASSPHRASE3):
            ret = sshx.handle_add(NAME3, HOST3, port=PORT3, user=USER3,
                                  password=PASSWORD3, identity=IDENTITY3)
            self.assertEqual(STATUS_SUCCESS, ret)

        # Account NAME4
        ret = sshx.handle_add(NAME4, HOST4,
                              port=PORT4,
                              user=USER4, password=PASSWORD4, identity=IDENTITY4)
        self.assertEqual(STATUS_SUCCESS, ret)

        # Account NAME5
        ret = sshx.handle_add(NAME5, HOST5,
                              port=PORT5,
                              user=USER5, password=PASSWORD5, identity=IDENTITY5)
        self.assertEqual(STATUS_SUCCESS, ret)

    def tearDown(self):
        _restore_all_sshx_handle()
        _teardown_config_dir()

    @mock.patch('pexpect.spawn', autospec=True)
    def test_connect(self, m):
        '''sshx connect <NAME1>'''
        sshx.handle_connect(NAME1)
        command = sshwrap._SSH_COMMAND_PASSWORD.format(
            user=USER1, host=HOST1, port=PORT1, identity=NOIDENTITY,
            extras='', forwards='', jump='', cmd='',
        )
        _assert_called_with(m, command)

        '''sshx connect <NAME2>'''
        sshx.handle_connect(NAME2)
        command = sshwrap._SSH_COMMAND_IDENTITY.format(
            user=USER2, host=HOST2, port=PORT2, identity=IDENTITY2,
            extras='', forwards='', jump='', cmd='',
        )
        _assert_called_with(m, command)

    # mock the __del__ to avoid deleting config file
    # mock the uuid to set the config file
    # mock spawn to get the executed command
    @mock.patch('sshx.sshwrap.AccountChain.__del__')
    @mock.patch('sshx.sshwrap.uuid.uuid4', return_value=_SSH_CONFIG_FILE)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_connect_via(self, m, m_uuid, m_del):
        '''sshx connect <NAME1> -v <NAME2>'''
        sshx.handle_connect(NAME1, via=f'{NAME2}')
        command = sshwrap._SSH_COMMAND_CONFIG.format(
            name=NAME1, extras=f'-F {SSH_CONFIG_FILE}',
            forwards='', cmd='', jump='')
        _assert_called_with(m, command)
        _assert_file_contains(self, SSH_CONFIG_FILE, f'Host {NAME2}')

        '''sshx connect <NAME1> -v <NAME3>,<NAME4>'''
        sshx.handle_connect(NAME1, via=f'{NAME3},{NAME4}')
        command = sshwrap._SSH_COMMAND_CONFIG.format(
            name=NAME1, extras=f'-F {SSH_CONFIG_FILE}',
            forwards='', cmd='', jump='')
        _assert_called_with(m, command)
        _assert_file_contains(
            self, SSH_CONFIG_FILE,
            [f'Host {NAME3}', f'Host {NAME4}',
             f'IdentityFile {IDENTITY3}'])

    @mock.patch('sshx.sshwrap.SSHPexpect.daemonize', return_value=False)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_forward(self, m, m_daemon):
        '''sshx forward <NAME1> -f <FORWARD1>'''
        sshx.handle_forward(NAME1, maps=(FORWARD1,))
        command = sshwrap._SSH_COMMAND_PASSWORD.format(
            user=USER1, host=HOST1, port=PORT1, identity=NOIDENTITY,
            extras='-NT', forwards=f'-L {FORWARD1}', jump='', cmd='',
        )
        _assert_called_with(m, command)
        m_daemon.assert_not_called()

        '''sshx forward <NAME1> -b -f <FORWARD1>'''
        sshx.handle_forward(NAME1, maps=(FORWARD1,), background=True)
        command = sshwrap._SSH_COMMAND_PASSWORD.format(
            user=USER1, host=HOST1, port=PORT1, identity=NOIDENTITY,
            extras='-NT', forwards=f'-L {FORWARD1}', jump='', cmd='',
        )
        _assert_called_with(m, command)
        m_daemon.assert_called_once()

    @mock.patch('sshx.sshwrap.AccountChain.__del__')
    @mock.patch('sshx.sshwrap.uuid.uuid4', return_value=_SSH_CONFIG_FILE)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_forward_via(self, m, m_uuid, m_del):
        '''sshx forward <NAME1> -v <NAME4> -f <FORWARD1>'''
        sshx.handle_forward(NAME1, maps=(FORWARD1,), via=NAME4)
        command = sshwrap._SSH_COMMAND_CONFIG.format(
            name=NAME1, extras=f'-NT -F {SSH_CONFIG_FILE}',
            forwards=f'-L {FORWARD1}', cmd='', jump='')
        _assert_called_with(m, command)
        _assert_file_contains(self, SSH_CONFIG_FILE, f'Host {NAME4}')

        '''sshx forward <NAME1> -v <NAME4>,<NAME5> -f <FORWARD1>'''
        sshx.handle_forward(NAME1, maps=(FORWARD1,), via=f'{NAME4},{NAME5}')
        command = sshwrap._SSH_COMMAND_CONFIG.format(
            name=NAME1, extras=f'-NT -F {SSH_CONFIG_FILE}',
            forwards=f'-L {FORWARD1}', cmd='', jump='')
        _assert_called_with(m, command)
        _assert_file_contains(self, SSH_CONFIG_FILE,
                              [f'Host {NAME4}', f'Host {NAME5}'])

    @mock.patch('pexpect.spawn', autospec=True)
    def test_scp(self, m):
        '''sshx scp <DIR1> <NAME1>:<DIR2>'''
        sshx.handle_scp(DIR1, f'{NAME1}:{DIR2}')
        command = sshwrap._SCP_COMMAND_PASSWORD.format(
            port=PORT1, jump='',
            src=DIR1, dst=f'{USER1}@{HOST1}:{DIR2}',
        )
        _assert_called_with(m, command)

    @mock.patch('sshx.sshwrap.AccountChain.__del__')
    @mock.patch('sshx.sshwrap.uuid.uuid4', return_value=_SSH_CONFIG_FILE)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_scp_via(self, m, m_uuid, m_del):
        '''sshx scp -v <NAME4> <DIR1> <NAME1>:<DIR2>'''
        sshx.handle_scp(DIR1, f'{NAME1}:{DIR2}', via=NAME4)
        command = sshwrap._SCP_COMMAND_CONFIG.format(
            name=NAME1, extras=f'-F {SSH_CONFIG_FILE}', jump='',
            src=DIR1, dst=f'{NAME1}:{DIR2}')
        _assert_called_with(m, command)
        _assert_file_contains(self, SSH_CONFIG_FILE, f'Host {NAME4}')

        '''sshx scp -v <NAME3>,<NAME4> <DIR1> <NAME1>:<DIR2>'''
        sshx.handle_scp(DIR1, f'{NAME1}:{DIR2}', via=f'{NAME3},{NAME4}')
        command = sshwrap._SCP_COMMAND_CONFIG.format(
            name=NAME1, extras=f'-F {SSH_CONFIG_FILE}', jump='',
            src=DIR1, dst=f'{NAME1}:{DIR2}')
        _assert_called_with(m, command)
        _assert_file_contains(self, SSH_CONFIG_FILE,
                              [f'Host {NAME3}', f'Host {NAME4}',
                               f'IdentityFile {IDENTITY3}'])

    @mock.patch('pexpect.spawn', autospec=True)
    def test_scp2(self, m):
        '''sshx scp2 <DIR1> <NAME1>:<DIR2>'''
        sshx.handle_scp(DIR1, f'{NAME1}:{DIR2}', with_forward=True)
        command = sshwrap._SCP_COMMAND_PASSWORD.format(
            port=PORT1, jump='',
            src=DIR1, dst=f'{USER1}@{HOST1}:{DIR2}',
        )
        _assert_called_with(m, command)

    @mock.patch('sshx.sshwrap.SSHPexpect.interactive', return_value=STATUS_SUCCESS)
    @mock.patch('sshx.sshwrap.find_available_port', return_value=LOCALPORT)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_scp2_via(self, m, m_findport, m_interact):
        '''sshx scp2 -v <NAME4> <DIR1> <NAME1>:<DIR2>'''
        sshx.handle_scp(DIR1, f'{NAME1}:{DIR2}', via=NAME4, with_forward=True)

        command1 = sshwrap._SSH_COMMAND_PASSWORD.format(
            user=USER4, host=HOST4, port=PORT4, identity=IDENTITY4,
            extras='-NT', forwards=f'-L {sshwrap.LOCALHOST}:{LOCALPORT}:{HOST1}:{PORT1}', jump='', cmd='',
        )

        command2 = sshwrap._SCP_COMMAND_PASSWORD.format(
            port=LOCALPORT, jump='',
            src=DIR1, dst=f'{USER1}@{sshwrap.LOCALHOST}:{DIR2}',
        )

        _assert_called_with_n(self, m, (command1, command2))

    # mock interactive to pretend the forwarding was successfully established,
    # otherwise interactive would failed because there's no real ssh connection.
    @mock.patch('sshx.sshwrap.AccountChain.__del__')
    @mock.patch('sshx.sshwrap.uuid.uuid4', return_value=_SSH_CONFIG_FILE)
    @mock.patch('sshx.sshwrap.SSHPexpect.interactive', return_value=STATUS_SUCCESS)
    @mock.patch('sshx.sshwrap.find_available_port', return_value=LOCALPORT)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_scp2_via2(self, m, m_findport, m_interact, m_uuid, m_del):
        '''sshx scp2 -v <NAME4>,<NAME5> <DIR1> <NAME1>:<DIR2>'''
        sshx.handle_scp(DIR1, f'{NAME1}:{DIR2}',
                        via=f'{NAME4},{NAME5}', with_forward=True)

        command1 = sshwrap._SSH_COMMAND_CONFIG.format(
            name=NAME5, extras=f'-NT -F {SSH_CONFIG_FILE}', cmd='', jump='',
            forwards=f'-L {sshwrap.LOCALHOST}:{LOCALPORT}:{HOST1}:{PORT1}')
        _assert_file_contains(self, SSH_CONFIG_FILE, f'Host {NAME4}')

        command2 = sshwrap._SCP_COMMAND_PASSWORD.format(
            port=LOCALPORT, jump='',
            src=DIR1, dst=f'{USER1}@{sshwrap.LOCALHOST}:{DIR2}',
        )

        _assert_called_with_n(self, m, (command1, command2))

    @mock.patch('sshx.utils.read_passphrase', return_value=PASSPHRASE3)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_socks(self, m, m_read):
        '''sshx socks <NAME1>'''
        sshx.handle_socks(NAME1)
        command = sshwrap._SSH_COMMAND_PASSWORD.format(
            user=USER1, host=HOST1, port=PORT1, identity=NOIDENTITY,
            extras='-D 1080 -NT', forwards='', jump='', cmd='',
        )
        _assert_called_with(m, command)

    @mock.patch('pexpect.spawn', autospec=True)
    def test_exec(self, m):
        '''sshx exec --tty <NAME1> -- <COMMAND1>'''
        sshx.handle_exec(NAME1, cmd=COMMAND1.split(), tty=True)
        command = sshwrap._SSH_COMMAND_PASSWORD.format(
            user=USER1, host=HOST1, port=PORT1, identity=NOIDENTITY,
            extras='-t', forwards='', jump='', cmd=COMMAND1,
        )
        _assert_called_with(m, command)

    @mock.patch('sshx.sshwrap.AccountChain.__del__')
    @mock.patch('sshx.sshwrap.uuid.uuid4', return_value=_SSH_CONFIG_FILE)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_exec_via(self, m, m_uuid, m_del):
        '''sshx exec <NAME1> -v <NAME4>,<NAME5> -- <COMMAND1>'''
        sshx.handle_exec(NAME1, cmd=COMMAND1.split(), via=f'{NAME4},{NAME5}')
        command = sshwrap._SSH_COMMAND_CONFIG.format(
            name=NAME1, extras=f'-F {SSH_CONFIG_FILE}',
            forwards='', cmd=COMMAND1, jump='')
        _assert_called_with(m, command)
        _assert_file_contains(self, SSH_CONFIG_FILE,
                              [f'Host {NAME4}', f'Host {NAME5}'])

    @mock.patch('pexpect.spawn', autospec=True)
    def test_copyid(self, m):
        '''sshx copyid <PUBKEY> <NAME1>'''
        sshx.handle_copyid(NAME1, PUBKEY)
        command = sshwrap._SSH_COPYID.format(
            user=USER1, host=HOST1, port=PORT1,
            identity=PUBKEY, extras='')
        _assert_called_with(m, command)

    @mock.patch('sshx.sshwrap.AccountChain.__del__')
    @mock.patch('sshx.sshwrap.uuid.uuid4', return_value=_SSH_CONFIG_FILE)
    @mock.patch('sshx.sshwrap.SSHPexpect.interactive', return_value=STATUS_SUCCESS)
    @mock.patch('sshx.sshwrap.find_available_port', return_value=LOCALPORT)
    @mock.patch('pexpect.spawn', autospec=True)
    def test_copyid_via(self, m, m_find, m_interact, m_uuid, m_del):
        '''sshx copyid <PUBKEY> <NAME1> -v <NAME4>,<NAME5>'''
        sshx.handle_copyid(NAME1, PUBKEY, via=f'{NAME4},{NAME5}')

        command1 = sshwrap._SSH_COMMAND_CONFIG.format(
            name=NAME5, extras=f'-NT -F {SSH_CONFIG_FILE}', cmd='', jump='',
            forwards=f'-L {sshwrap.LOCALHOST}:{LOCALPORT}:{HOST1}:{PORT1}')
        _assert_file_contains(self, SSH_CONFIG_FILE, f'Host {NAME4}')

        command2 = sshwrap._SSH_COPYID.format(
            user=USER1, host=sshwrap.LOCALHOST, port=LOCALPORT,
            identity=PUBKEY, extras='')
        _assert_called_with_n(self, m, (command1, command2))


global_test_init()

if __name__ == '__main__':
    unittest.main()
