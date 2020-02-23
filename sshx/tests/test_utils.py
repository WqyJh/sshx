import os
import mock
import unittest

from .. import utils

BASEDIR = os.path.dirname(__file__)
IDENTITY1 = os.path.join(BASEDIR, 'data/rsa1')
IDENTITY2 = os.path.join(BASEDIR, 'data/rsa2')
PASSPHRASE2 = '12345678'


class UtilsTest(unittest.TestCase):
    def test_sshkey_has_passphrase(self):
        self.assertFalse(utils.sshkey_has_passphrase(IDENTITY1))
        self.assertTrue(utils.sshkey_has_passphrase(IDENTITY2))

    def test_sshkey_check_passphrase(self):
        self.assertTrue(utils.sshkey_check_passphrase(IDENTITY1, ''))
        self.assertFalse(utils.sshkey_check_passphrase(IDENTITY1, PASSPHRASE2))

        self.assertTrue(utils.sshkey_check_passphrase(IDENTITY2, PASSPHRASE2))
        self.assertFalse(utils.sshkey_check_passphrase(IDENTITY2, ''))


if __name__ == "__main__":
    unittest.main()
