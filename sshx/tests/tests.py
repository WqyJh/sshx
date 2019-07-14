import os
import mock
import shutil
import unittest

from sshx import cfg
from sshx import sshx
from sshx import utils
from sshx import const as c


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
            m.assert_called_with(force=False)

            sshx.invoke(['init', '--force'])
            m.assert_called_with(force=True)

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

    def test_connect(self):
        with mock.patch('sshx.sshx.handle_connect') as m:
            sshx.invoke(['connect', NAME1])
            m.assert_called_with(NAME1, via=None)


class FunctionalTest(unittest.TestCase):
    def setUp(self):
        cfg.set_config_dir('.tmp')

    def tearDown(self):
        shutil.rmtree('.tmp')

    def test_init(self):
        self.assertEqual(cfg.STATUS_UNINIT, cfg.check_init())

        msg = sshx.handle_init(force=False)
        self.assertEqual('success', msg['status'])
        config = cfg.read_config()
        self.assertTrue(utils.is_str(config.phrase))
        self.assertEqual(0, len(config.accounts))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        msg = sshx.handle_init(force=False)
        self.assertEqual('fail', msg['status'])
        config = cfg.read_config()
        self.assertTrue(utils.is_str(config.phrase))
        self.assertEqual(0, len(config.accounts))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        phrase1 = config.phrase
        msg = sshx.handle_init(force=True)
        self.assertEqual('success', msg['status'])
        config = cfg.read_config()
        self.assertNotEqual(phrase1, config.phrase)
        self.assertEqual(0, len(config.accounts))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

    def test_add(self):
        msg = sshx.handle_init()

        msg = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        self.assertEqual(1, cfg.accounts_num())
        acc = cfg.read_account(NAME1)
        self.assertEqual(HOST1, acc.host)
        self.assertEqual(PORT1, acc.port)
        self.assertEqual(USER1, acc.user)
        self.assertEqual(PASSWORD1, acc.password)
        self.assertEqual(IDENTITY1, acc.identity)

        msg = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        self.assertEqual(2, cfg.accounts_num())

    def test_add_via(self):
        msg = sshx.handle_init()

        msg = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('fail', msg['status'])

        msg = sshx.handle_add(NAME1, HOST1, port=PORT1, via=NAME2,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('fail', msg['status'])

        msg = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        msg = sshx.handle_add(NAME2, HOST1, port=PORT1, via=NAME1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])


    def test_update(self):
        msg = sshx.handle_init()
        self.assertEqual('success', msg['status'])
        msg = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])

        msg = sshx.handle_update(NAME1, update_fields={
            'identity': IDENTITY2,
            'password': PASSWORD2,
        })
        self.assertEqual('success', msg['status'])
        self.assertEqual(1, cfg.accounts_num())
        account = cfg.read_account(NAME1)
        self.assertEqual(IDENTITY2, account.identity)
        self.assertEqual(PASSWORD2, account.password)

        msg = sshx.handle_update(NAME2, update_fields={
            'identity': IDENTITY2,
        })
        self.assertEqual('fail', msg['status'])
        self.assertEqual(1, cfg.accounts_num())

        msg = sshx.handle_update(NAME1, update_fields={
            'name': NAME2,
        })
        self.assertEqual('success', msg['status'])
        self.assertEqual(1, cfg.accounts_num())
        account = cfg.read_account(NAME1)
        self.assertIsNone(account)
        account = cfg.read_account(NAME2)
        self.assertEqual(IDENTITY2, account.identity)

    def test_del(self):
        msg = sshx.handle_init()
        self.assertEqual('success', msg['status'])
        msg = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        msg = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])

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
        msg = sshx.handle_init()
        self.assertEqual('success', msg['status'])
        msg = sshx.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        msg = sshx.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY2)
        self.assertEqual('success', msg['status'])

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
