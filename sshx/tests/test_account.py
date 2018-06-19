from __future__ import unicode_literals

import unittest
from sshx.account import *


ACCOUNT1 = {
    'name': 'a1',
    'host': 'h1',
}

ACCOUNT2 = {
    'name': 'a2',
    'host': 'h2',
}

ACCOUNT3 = {
    'name': 'a1',
    'host': 'h3',
}

ACCOUNT4 = {
    'name': 'a4',
    'host': 'h4',
}


class AccountTest(unittest.TestCase):
    def setUp(self):
        self.list1 = [ACCOUNT1, ACCOUNT2]
        self.list2 = [ACCOUNT1, ACCOUNT2, ACCOUNT3]

    def test_find(self):
        account1 = find_by_name(self.list1, ACCOUNT1['name'])
        self.assertEqual(ACCOUNT1['host'], account1['host'])
        account2 = find_by_name(self.list2, ACCOUNT2['name'])
        self.assertEqual(ACCOUNT2['host'], account2['host'])

    def test_add_or_update(self):
        add_or_update(self.list1, ACCOUNT3)
        self.assertEqual(2, len(self.list1))
        self.assertEqual(find_by_name(self.list1, ACCOUNT1['name'])[
                         'host'], ACCOUNT3['host'])

        add_or_update(self.list1, ACCOUNT4)
        self.assertEqual(3, len(self.list1))


if __name__ == '__main__':
    unittest.main()