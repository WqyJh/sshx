from __future__ import unicode_literals

import unittest

from sshx import tokenizer


class TokenizerTest(unittest.TestCase):
    def test_encrypt_decrypt(self):
        s = 'hello'
        k = 'key'
        t = tokenizer.encrypt(s, k)
        self.assertNotEqual(s, t)
        self.assertEqual(s, tokenizer.decrypt(t, k))