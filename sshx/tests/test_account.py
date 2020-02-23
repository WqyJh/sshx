from . import global_test_init
import unittest
from sshx.account import *


class AccountTest(unittest.TestCase):
    def setUp(self):
        self.ACCOUNT1 = Account(name='a1', host='h1')
        self.ACCOUNT2 = Account(name='a2', host='h2')
        self.ACCOUNT3 = Account(name='a1', host='h3')
        self.ACCOUNT4 = Account(name='a4', host='h4')

        self.list1 = [self.ACCOUNT1, self.ACCOUNT2]
        self.list2 = [self.ACCOUNT1, self.ACCOUNT2, self.ACCOUNT3]

    def test_find(self):
        account1 = find_by_name(self.list1, self.ACCOUNT1.name)
        self.assertEqual(self.ACCOUNT1.host, account1.host)
        account2 = find_by_name(self.list2, self.ACCOUNT2.name)
        self.assertEqual(self.ACCOUNT2.host, account2.host)

    def test_add_or_update(self):
        add_or_update(self.list1, self.ACCOUNT3)
        self.assertEqual(2, len(self.list1))
        self.assertEqual(find_by_name(self.list1, self.ACCOUNT1.name).host,
                         self.ACCOUNT1.host)

        '''
        add_or_update() may change the value of the original account,
        therefore, the original account can't be declared as global value.
        '''
        add_or_update(self.list1, self.ACCOUNT4)
        self.assertEqual(3, len(self.list1))

    def test_eq(self):
        self.assertNotEqual(self.ACCOUNT1, self.ACCOUNT2)
        self.assertNotEqual(self.ACCOUNT1, self.ACCOUNT3)

        account = Account(name='a1', host='h1')
        self.assertEqual(self.ACCOUNT1, account)


global_test_init()

if __name__ == '__main__':
    unittest.main()
