import unittest

from sshx import tokenizer


class TokenizerTest(unittest.TestCase):
    def test_encrypt_decrypt(self):
        s = 'hello'
        k = 'key'
        t = tokenizer.encrypt(s, k)
        self.assertNotEqual(s, t)
        self.assertEqual(s, tokenizer.decrypt(t, k))

    def test_encrypt_decrypt_multiple_times(self):
        data = {
            'hello1': 'key1',
            'hello2': 'key2',
            'hello3': 'key3',
        }

        for s, k in data.items():
            t = tokenizer.encrypt(s, k)
            self.assertNotEqual(s, t)
            self.assertEqual(s, tokenizer.decrypt(t, k))