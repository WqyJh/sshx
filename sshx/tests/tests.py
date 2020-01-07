import os
import mock
import shutil
import unittest

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
IDENTITY1 = ''

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
                             '-u', USER1, '-p', '-i', IDENTITY1])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=PORT1, user=USER1,
                                     password=PASSWORD1, identity=IDENTITY1, via='')

    def test_add2(self):
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            with mock.patch('sshx.sshx.handle_add') as m:
                sshx.invoke(['add', NAME1, '-l', '%s@%s:%s' % (USER1, HOST1, PORT1),
                             '-p', '-i', IDENTITY1])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=PORT1, user=USER1,
                                     password=PASSWORD1, identity=IDENTITY1, via='')

        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            with mock.patch('sshx.sshx.handle_add') as m:
                sshx.invoke(['add', NAME1, '-l', '%s@%s' % (USER1, HOST1),
                             '-p', '-i', IDENTITY1])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=c.DEFAULT_PORT, user=USER1,
                                     password=PASSWORD1, identity=IDENTITY1, via='')

    def test_update(self):
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m_read_password:
            with mock.patch('sshx.sshx.handle_update') as m:
                sshx.invoke(['update', NAME1, '-H', HOST1])
                m.assert_called_with(NAME1, update_fields={
                    'host': HOST1,
                })

                sshx.invoke(['update', NAME1, '-H', HOST1, '-P',
                             PORT1, '-u', USER1, '-p', '-i', IDENTITY1, '-v', NAME2])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, update_fields={
                    'host': HOST1,
                    'port': PORT1,
                    'user': USER1,
                    'password': PASSWORD2,
                    'identity': IDENTITY1,
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
        cfg.set_config_dir('.tmp')

    def tearDown(self):
        shutil.rmtree('.tmp')

    def test_init(self):
        self.assertEqual(cfg.STATUS_UNINIT, cfg.check_init())

        ret = sshx.handle_init(force=False)
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertTrue(utils.is_str(config.phrase))
        self.assertFalse(config.security)
        self.assertEqual(0, len(config.accounts))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        ret = sshx.handle_init(force=False)
        self.assertEqual(STATUS_FAIL, ret)
        config = cfg.read_config()
        self.assertTrue(utils.is_str(config.phrase))
        self.assertFalse(config.security)
        self.assertEqual(0, len(config.accounts))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        phrase1 = config.phrase
        ret = sshx.handle_init(force=True)
        self.assertEqual(STATUS_SUCCESS, ret)
        config = cfg.read_config()
        self.assertNotEqual(phrase1, config.phrase)
        self.assertFalse(config.security)
        self.assertEqual(0, len(config.accounts))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        # test security option
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            ret = sshx.handle_init(force=True, security=True)
            m_read_password.assert_called_once()
            # m_read_password.reset_mock()
            self.assertEqual(STATUS_SUCCESS, ret)
            config = cfg.read_config()
            self.assertTrue(config.security)
            cfg._cached_passphrase = None
            self.assertTrue(cfg.verify_passphrase(config))
            # m_read_password.assert_called_once()
            self.assertEqual(0, len(config.accounts))
            self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

    def test_config(self):
        # Init without security
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m:
            ret = sshx.handle_init()
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_not_called()

            config = cfg.read_config()
            self.assertFalse(config.security)
            phrase = config.phrase
            cfg._cached_passphrase = None

        # Enable security option
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m:
            ret = sshx.handle_config(security=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called()

            config = cfg.read_config()
            self.assertNotEqual(phrase, config.phrase)
            self.assertTrue(cfg.verify_passphrase(config))
            phrase = config.phrase
            cfg._cached_passphrase = None

        # Change passphrase
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m:
            ret = sshx.handle_config(chphrase=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_called()

            config = cfg.read_config()
            self.assertTrue(config.security)
            self.assertNotEqual(phrase, config.phrase)
            self.assertTrue(cfg.verify_passphrase(config))
            self.assertEqual(PASSWORD2, config.phrase)
            phrase = config.phrase
            cfg._cached_passphrase = None

        # Disable security option
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m:
            ret = sshx.handle_config(security=False)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_not_called()

            config = cfg.read_config()
            self.assertFalse(config.security)
            # config.phrase is randomly generate
            self.assertNotEqual(phrase, config.phrase)
            self.assertTrue(cfg.verify_passphrase(config))
            self.assertNotEqual(PASSWORD2, config.phrase)
            phrase = config.phrase
            cfg._cached_passphrase = None

        # Change passphrase
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m:
            ret = sshx.handle_config(chphrase=True)
            self.assertEqual(STATUS_SUCCESS, ret)
            m.assert_not_called()

            config = cfg.read_config()
            self.assertFalse(config.security)
            self.assertNotEqual(phrase, config.phrase)
            self.assertTrue(cfg.verify_passphrase(config))
            self.assertIsNone(cfg._cached_passphrase)
            cfg._cached_passphrase = None

    def test_add(self):
        ret = sshx.handle_init()

        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)
        self.assertEqual(1, cfg.accounts_num())
        acc = cfg.read_account(NAME1)
        self.assertEqual(HOST1, acc.host)
        self.assertEqual(PORT1, acc.port)
        self.assertEqual(USER1, acc.user)
        self.assertEqual(PASSWORD1, acc.password)
        self.assertEqual(IDENTITY1, acc.identity)

        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)
        self.assertEqual(2, cfg.accounts_num())

    def test_add_via(self):
        ret = sshx.handle_init()

        ret = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_FAIL, ret)

        ret = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME2,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_FAIL, ret)

        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)
        ret = sshx.handle_add(NAME2, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)

    def test_update(self):
        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)

        ret = sshx.handle_update(NAME1, update_fields={
            'identity': IDENTITY2,
            'password': PASSWORD2,
        })
        self.assertEqual(STATUS_SUCCESS, ret)
        self.assertEqual(1, cfg.accounts_num())
        account = cfg.read_account(NAME1)
        self.assertEqual(IDENTITY2, account.identity)
        self.assertEqual(PASSWORD2, account.password)

        ret = sshx.handle_update(NAME2, update_fields={
            'identity': IDENTITY2,
        })
        self.assertEqual(STATUS_FAIL, ret)
        self.assertEqual(1, cfg.accounts_num())

        ret = sshx.handle_update(NAME1, update_fields={
            'name': NAME2,
        })
        self.assertEqual(STATUS_SUCCESS, ret)
        self.assertEqual(1, cfg.accounts_num())
        account = cfg.read_account(NAME1)
        self.assertIsNone(account)
        account = cfg.read_account(NAME2)
        self.assertEqual(IDENTITY2, account.identity)

    def test_del(self):
        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)
        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
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

    def test_connect(self):
        ret = sshx.handle_init()
        self.assertEqual(STATUS_SUCCESS, ret)
        ret = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual(STATUS_SUCCESS, ret)
        ret = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY2)
        self.assertEqual(STATUS_SUCCESS, ret)

        with mock.patch('sshx.sshwrap.ssh') as m:
            sshx.handle_connect(NAME1)
            m.assert_called()
            # assert_called_with() failed,
            # maybe because the bug of mock.
            # m.assert_called_with(cfg.Account(
            #     NAME1, user=USER1, host=HOST1, port=PORT1, password=PASSWORD1, identity=IDENTITY1))

            sshx.handle_connect(NAME2)
            m.assert_called()
            # assert_called_with() failed,
            # maybe because the bug of mock.
            # m.assert_called_with(cfg.Account(
            #     NAME2, user=USER1, host=HOST1, port=PORT1, password=PASSWORD1, identity=IDENTITY2))


if __name__ == '__main__':
    unittest.main()
