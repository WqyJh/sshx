from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import unittest
from sshx.cfg import *


class ConfigTest(unittest.TestCase):
    def test_is_valid(self):
        c1 = Config({'phrase': '', 'accounts': []})
        self.assertTrue(c1.is_valid())


if __name__ == '__main__':
    unittest.main()