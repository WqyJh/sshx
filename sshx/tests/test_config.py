from . import global_test_init
import os
import unittest

from .. import cfg


class ConfigTest(unittest.TestCase):
    def test_is_valid(self):
        c1 = cfg.Config({'phrase': '', 'accounts': []})
        self.assertTrue(c1.is_valid())


class CfgTest(unittest.TestCase):
    def test_set_config_dir(self):
        config_dir = 'HEHE'
        cfg.set_config_dir(config_dir)
        self.assertEqual(config_dir, cfg.CONFIG_DIR)
        self.assertEqual(os.path.join(
            config_dir, cfg._ACCOUNT_FILE), cfg.ACCOUNT_FILE)


global_test_init()

if __name__ == '__main__':
    unittest.main()
