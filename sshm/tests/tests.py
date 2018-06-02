from __future__ import unicode_literals

import os
import mock
import shutil
import unittest

from sshm import cfg
from sshm import sshm
from sshm import utils


class UtilTest(unittest.TestCase):
    def test_set_config_dir(self):
        config_dir = 'HEHE'
        cfg.set_config_dir(config_dir)
        self.assertEqual(config_dir, cfg.CONFIG_DIR)
        self.assertEqual(os.path.join(config_dir, cfg._ACCOUNT_FILE), cfg.ACCOUNT_FILE)


NAME1 = 'name1'
HOST1 = 'host1'
PORT1 = 'port1'
USER1 = 'user1'
PASSWORD1 = 'password1'
IDENTITY1 = ''

NAME2 = 'name2'
IDENTITY2 = 'identity2'


class CommandTest(unittest.TestCase):

    def test_init(self):
        with mock.patch('sshm.sshm.handle_init') as m:
            sshm.invoke(['init', ])
            m.assert_called_with(force=False)

            sshm.invoke(['init', '--force'])
            m.assert_called_with(force=True)

    def test_add(self):
        with mock.patch('sshm.sshm.handle_add') as m:
            sshm.invoke(['add', '-n', NAME1, '-H', HOST1, '-p', PORT1,
                         '-u', USER1, '-P', PASSWORD1, '-i', IDENTITY1])
            m.assert_called_with(
                NAME1, HOST1, port=PORT1, user=USER1, password=PASSWORD1, identity=IDENTITY1)

    def test_update(self):
        with mock.patch('sshm.sshm.handle_update') as m:
            sshm.invoke(['update', '-n', NAME1, '-H', HOST1])
            m.assert_called_with(NAME1, update_fields={
                'host': HOST1,
            })

            sshm.invoke(['update', '-n', NAME1, '-H', HOST1, '-p',
                         PORT1, '-u', USER1, '-P', PASSWORD1, '-i', IDENTITY1])
            m.assert_called_with(NAME1, update_fields={
                'host': HOST1,
                'port': PORT1,
                'user': USER1,
                'password': PASSWORD1,
                'identity': IDENTITY1,
            })

    def test_del(self):
        with mock.patch('sshm.sshm.handle_del') as m:
            sshm.invoke(['del', NAME1])
            m.assert_called_with(NAME1)

    def test_connect(self):
        with mock.patch('sshm.sshm.handle_connect') as m:
            sshm.invoke(['connect', NAME1])
            m.assert_called_with(NAME1)


class FunctionalTest(unittest.TestCase):
    def setUp(self):
        cfg.set_config_dir('.sshm')

    def tearDown(self):
        shutil.rmtree('.sshm')

    def test_init(self):
        self.assertEqual(cfg.STATUS_UNINIT, cfg.check_init())

        msg = sshm.handle_init(force=False)
        self.assertEqual('success', msg['status'])
        config, acclist = cfg.read_config()
        self.assertTrue(utils.is_str(config['phrase']))
        self.assertEqual(0, len(acclist))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        msg = sshm.handle_init(force=False)
        self.assertEqual('fail', msg['status'])
        config, acclist = cfg.read_config()
        self.assertTrue(utils.is_str(config['phrase']))
        self.assertEqual(0, len(acclist))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

        phrase1 = config['phrase']
        msg = sshm.handle_init(force=True)
        self.assertEqual('success', msg['status'])
        config, acclist = cfg.read_config()
        self.assertNotEqual(phrase1, config['phrase'])
        self.assertEqual(0, len(acclist))
        self.assertEqual(cfg.STATUS_INITED, cfg.check_init())

    def test_add(self):
        msg = sshm.handle_init()

        msg = sshm.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        self.assertEqual(1, cfg.accounts_num())
        acc = cfg.read_account(NAME1)
        self.assertEqual(HOST1, acc['host'])
        self.assertEqual(PORT1, acc['port'])
        self.assertEqual(USER1, acc['user'])
        self.assertEqual(PASSWORD1, acc['password'])
        self.assertEqual(IDENTITY1, acc['identity'])

        msg = sshm.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        self.assertEqual(2, cfg.accounts_num())

    def test_update(self):
        msg = sshm.handle_init()
        self.assertEqual('success', msg['status'])
        msg = sshm.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])

        msg = sshm.handle_update(NAME1, update_fields={
            'identity': IDENTITY2,
        })
        self.assertEqual('success', msg['status'])
        self.assertEqual(1, cfg.accounts_num())
        account = cfg.read_account(NAME1)
        self.assertEqual(IDENTITY2, account['identity'])

        msg = sshm.handle_update(NAME2, update_fields={
            'identity': IDENTITY2,
        })
        self.assertEqual('fail', msg['status'])
        self.assertEqual(1, cfg.accounts_num())

        msg = sshm.handle_update(NAME1, update_fields={
            'name': NAME2,
        })
        self.assertEqual('success', msg['status'])
        self.assertEqual(1, cfg.accounts_num())
        account = cfg.read_account(NAME1)
        self.assertIsNone(account)
        account = cfg.read_account(NAME2)
        self.assertEqual(IDENTITY2, account['identity'])

    def test_del(self):
        msg = sshm.handle_init()
        self.assertEqual('success', msg['status'])
        msg = sshm.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        msg = sshm.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])

        config, acclist = cfg.read_config()
        self.assertEqual(2, len(acclist))

        sshm.handle_del(NAME1)
        config, acclist = cfg.read_config()
        self.assertEqual(1, len(acclist))
        self.assertIsNone(cfg.find_by_name(acclist, NAME1))

        sshm.handle_del(NAME2)
        config, acclist = cfg.read_config()
        self.assertEqual(0, len(acclist))
        self.assertIsNone(cfg.find_by_name(acclist, NAME2))

    def test_connect(self):
        msg = sshm.handle_init()
        self.assertEqual('success', msg['status'])
        msg = sshm.handle_add(NAME1, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY1)
        self.assertEqual('success', msg['status'])
        msg = sshm.handle_add(NAME2, HOST1, port=PORT1,
                              user=USER1, password=PASSWORD1, identity=IDENTITY2)
        self.assertEqual('success', msg['status'])

        with mock.patch('sshm.sshwrap.sshp') as m:
            sshm.handle_connect(NAME1)
            m.assert_called_with(HOST1, PORT1, USER1, PASSWORD1)

        with mock.patch('sshm.sshwrap.sshi') as m:
            sshm.handle_connect(NAME2)
            m.assert_called_with(HOST1, PORT1, USER1, IDENTITY2)


if __name__ == '__main__':
    unittest.main()
