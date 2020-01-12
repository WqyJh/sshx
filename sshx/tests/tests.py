import os
import mock
import shutil
import unittest

import lazy_object_proxy as lazy

from .. import cfg
from .. import sshx
from .. import utils
from .. import const as c
from ..const import STATUS_SUCCESS, STATUS_FAIL


class CfgTest(unittest.TestCase):
    def test_set_config_dir(self):
        config_dir = 'HEHE'
        cfg.set_config_dir(config_dir)
        self.assertEqual(config_dir, cfg.CONFIG_DIR)
        self.assertEqual(os.path.join(
            config_dir, cfg._ACCOUNT_FILE), cfg.ACCOUNT_FILE)


NAME1 = 'name1'
HOST1 = 'host1'
PORT1 = 'port1'
USER1 = 'user1'
PASSWORD1 = 'password1'
NOIDENTITY = ''

NAME2 = 'name2'
IDENTITY2 = 'identity2'
PASSWORD2 = 'password2'


class CommandTest(unittest.TestCase):
    def test_init(self):
        with mock.patch('sshx.sshx.handle_init') as m:
            sshx.invoke(['init', ])
            m.assert_called_with(force=False, security=False)

            sshx.invoke(['init', '--force'])
            m.assert_called_with(force=True, security=False)

            sshx.invoke(['init', '--force', '--security'])
            m.assert_called_with(force=True, security=True)

    def test_config(self):
        with mock.patch('sshx.sshx.handle_config') as m:
            sshx.invoke(['config', '--security-on'])
            m.assert_called_with(security=True, chphrase=False)

            sshx.invoke(['config', '--security-off'])
            m.assert_called_with(security=False, chphrase=False)

            sshx.invoke(['config', '--chphrase'])
            m.assert_called_with(security=None, chphrase=True)

    def test_add(self):
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            with mock.patch('sshx.sshx.handle_add') as m:
                sshx.invoke(['add', NAME1, '-H', HOST1, '-P', PORT1,
                             '-u', USER1, '-p', '-i', NOIDENTITY])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=PORT1, user=USER1,
                                     password=PASSWORD1, identity=NOIDENTITY, via='')

    def test_add2(self):
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            with mock.patch('sshx.sshx.handle_add') as m:
                sshx.invoke(['add', NAME1, '-l', '%s@%s:%s' % (USER1, HOST1, PORT1),
                             '-p', '-i', NOIDENTITY])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=PORT1, user=USER1,
                                     password=PASSWORD1, identity=NOIDENTITY, via='')

        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            with mock.patch('sshx.sshx.handle_add') as m:
                sshx.invoke(['add', NAME1, '-l', '%s@%s' % (USER1, HOST1),
                             '-p', '-i', NOIDENTITY])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=c.DEFAULT_PORT, user=USER1,
                                     password=PASSWORD1, identity=NOIDENTITY, via='')

    def test_update(self):
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m_read_password:
            with mock.patch('sshx.sshx.handle_update') as m:
                sshx.invoke(['update', NAME1, '-H', HOST1])
                m.assert_called_with(NAME1, update_fields={
                    'host': HOST1,
                })

                sshx.invoke(['update', NAME1, '-H', HOST1, '-P',
                             PORT1, '-u', USER1, '-p', '-i', NOIDENTITY, '-v', NAME2])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, update_fields={
                    'host': HOST1,
                    'port': PORT1,
                    'user': USER1,
                    'password': PASSWORD2,
                    'identity': NOIDENTITY,
                    'via': NAME2,
                })

    def test_del(self):
        with mock.patch('sshx.sshx.handle_del') as m:
            sshx.invoke(['del', NAME1])
            m.assert_called_with(NAME1)

    def test_list(self):
        with mock.patch('sshx.sshx.handle_list') as m:
            sshx.invoke(['list', ])
            m.assert_called_with(key='name', reverse=False)

            sshx.invoke(['list', '--sort', 'host'])
            m.assert_called_with(key='host', reverse=False)

            sshx.invoke(['list', '--reverse'])
            m.assert_called_with(key='name', reverse=True)

    def test_show(self):
        with mock.patch('sshx.sshx.handle_show') as m:
            sshx.invoke(['show', NAME1])
            m.assert_called_with(NAME1, password=False)

            sshx.invoke(['show', NAME1, '-p'])
            m.assert_called_with(NAME1, password=True)

    def test_connect(self):
        with mock.patch('sshx.sshx.handle_connect') as m:
            sshx.invoke(['connect', NAME1])
            m.assert_called_with(NAME1, via=None)

    def test_forward(self):
        rc = sshx.invoke(['forward', NAME1])
        self.assertEqual(c.STATUS_FAIL, rc)

        FORWARD1 = ':8000:127.0.0.1:8000'
        RFORWARD1 = '127.0.0.1:9000:127.0.0.1:9000'
        with mock.patch('sshx.sshx.handle_forward') as m:
            sshx.invoke(['forward', NAME1, '-f', FORWARD1])
            m.assert_called_with(NAME1, background=False,
                                 maps=(FORWARD1,), rmaps=(), via=None)

            sshx.invoke(['forward', NAME1, '-rf', RFORWARD1])
            m.assert_called_with(NAME1, background=False,
                                 maps=(), rmaps=(RFORWARD1,), via=None)

            sshx.invoke(['forward', NAME1, '-f', FORWARD1, '-rf', RFORWARD1])
            m.assert_called_with(NAME1, background=False, maps=(
                FORWARD1,), rmaps=(RFORWARD1,), via=None)

            sshx.invoke(['forward', NAME1, '-f', FORWARD1, '-b'])
            m.assert_called_with(NAME1, background=True,
                                 maps=(FORWARD1,), rmaps=(), via=None)

    def test_socks(self):
        with mock.patch('sshx.sshx.handle_socks') as m:
            sshx.invoke(['socks', NAME1])
            m.assert_called_with(NAME1, via=None, port=1080, background=False)

            sshx.invoke(['socks', NAME1, '-p', 1081])
            m.assert_called_with(NAME1, via=None, port=1081, background=False)

            sshx.invoke(['socks', NAME1, '-b'])
            m.assert_called_with(NAME1, via=None, port=1080, background=True)

    def test_scp(self):
        with mock.patch('sshx.sshx.handle_scp') as m:
            sshx.invoke(['scp', 'SRC', 'DST'])
            m.assert_called_with('SRC', 'DST', via=None)

    def test_exec(self):
        with mock.patch('sshx.sshx.handle_exec') as m:
            sshx.invoke(['exec', NAME1, '--tty', '--', 'ls', '-al'])
            m.assert_called_with(NAME1, via=None, tty=True, exec=('ls', '-al'))


class FunctionalTest(unittest.TestCase):
    def setUp(self):
        sshx._reset()
        cfg.set_config_dir('.tmp')

    def tearDown(self):
        shutil.rmtree('.tmp')

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

        sshx._reset()
        ret = sshx.handle_init()
        self.assertEqual(STATUS_FAIL, ret)
        config = cfg.read_config()
        self.assertTrue(utils.is_str(config.phrase))
        self.assertFalse(config.security)
        self.assertEqual(0, len(config.accounts))
        self.assertIsNotNone(config.get_passphrase())
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())
        phrase = config.phrase

        sshx._reset()
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
            sshx._reset()
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
            sshx._reset()
            ret = sshx.handle_config(security=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called()

            config = cfg.read_config()
            self.assertIsNotNone(config.get_passphrase())
            self.assertEqual(PASSWORD1, config._phrase)

        # Change passphrase
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m:
            sshx._reset()
            ret = sshx.handle_config(chphrase=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called()

            config = cfg.read_config()
            self.assertTrue(config.security)
            self.assertIsNotNone(config.get_passphrase())
            self.assertEqual(PASSWORD2, config._phrase)

        # Disable security option
        with mock.patch('sshx.utils.random_str', return_value=PASSWORD1) as m:
            sshx._reset()
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
            sshx._reset()
            ret = sshx.handle_config(chphrase=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called_once()

            config = cfg.read_config()
            self.assertFalse(config.security)
            self.assertIsNotNone(config.get_passphrase())
            self.assertNotEqual(phrase, config.phrase)

    def test_add(self):
        ret = sshx.handle_init()

        sshx._reset()
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

        sshx._reset()
        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertEqual(2, len(config.accounts))

    def test_add_via(self):
        ret = sshx.handle_init()

        sshx._reset()
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_FAIL, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME2,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_FAIL, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME2, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

    def test_update(self):
        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
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

        sshx._reset()
        ret = sshx.handle_update(NAME2, update_fields={
            'identity': IDENTITY2,
        })
        self.assertEqual(STATUS_FAIL, ret)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))

        sshx._reset()
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
        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        config = cfg.read_config()
        self.assertEqual(2, len(config.accounts))

        sshx._reset()
        sshx.handle_del(NAME1)
        config = cfg.read_config()
        self.assertEqual(1, len(config.accounts))
        self.assertIsNone(cfg.find_by_name(config.accounts, NAME1))

        sshx._reset()
        sshx.handle_del(NAME2)
        config = cfg.read_config()
        self.assertEqual(0, len(config.accounts))
        self.assertIsNone(cfg.find_by_name(config.accounts, NAME2))

    @mock.patch('pexpect.spawn', autospec=True)
    def test_connect(self, m):
        from .. import sshwrap
        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=NOIDENTITY)
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY2)
        self.assertEqual(STATUS_SUCCESS, ret)

        sshx._reset()
        sshx.handle_connect(NAME1)
        m.assert_called_with(sshwrap._SSH_COMMAND_PASSWORD.format(
            user=USER1, host=HOST1, port=PORT1, identity=NOIDENTITY,
            extras='', forwards='', jump='', exec='',
        ))
        # m.expect.assert_called()
        # m.sendline.assert_called_with(PASSWORD1)

        sshx._reset()
        sshx.handle_connect(NAME2)
        m.assert_called()
        m.assert_called_with(sshwrap._SSH_COMMAND_IDENTITY.format(
            user=USER1, host=HOST1, port=PORT1, identity=IDENTITY2,
            extras='', forwards='', jump='', exec='',
        ))

if __name__ == '__main__':
    unittest.main()
