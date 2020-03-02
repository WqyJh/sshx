# -*- coding: future_fstrings -*-

from . import global_test_init
import mock
import unittest

from .. import sshx
from .. import const as c


NAME1 = 'name1'
HOST1 = 'host1'
PORT1 = 'port1'
USER1 = 'user1'
PASSWORD1 = 'password1'
NOIDENTITY = ''

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
                             '-u', USER1, '-p', '-i', NOIDENTITY])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=PORT1, user=USER1,
                                     password=PASSWORD1, identity=NOIDENTITY, via='')

    def test_add2(self):
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            with mock.patch('sshx.sshx.handle_add') as m:
                sshx.invoke(['add', NAME1, '-l', '%s@%s:%s' % (USER1, HOST1, PORT1),
                             '-p', '-i', NOIDENTITY])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=PORT1, user=USER1,
                                     password=PASSWORD1, identity=NOIDENTITY, via='')

        with mock.patch('sshx.utils.read_password', return_value=PASSWORD1) as m_read_password:
            with mock.patch('sshx.sshx.handle_add') as m:
                sshx.invoke(['add', NAME1, '-l', '%s@%s' % (USER1, HOST1),
                             '-p', '-i', NOIDENTITY])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, HOST1, port=c.DEFAULT_PORT, user=USER1,
                                     password=PASSWORD1, identity=NOIDENTITY, via='')

    def test_update(self):
        with mock.patch('sshx.utils.read_password', return_value=PASSWORD2) as m_read_password:
            with mock.patch('sshx.sshx.handle_update') as m:
                sshx.invoke(['update', NAME1, '-H', HOST1])
                m.assert_called_with(NAME1, update_fields={
                    'host': HOST1,
                })

                sshx.invoke(['update', NAME1, '-H', HOST1, '-P',
                             PORT1, '-u', USER1, '-p', '-i', NOIDENTITY, '-v', NAME2])
                m_read_password.assert_called_once()
                m.assert_called_with(NAME1, update_fields={
                    'host': HOST1,
                    'port': PORT1,
                    'user': USER1,
                    'password': PASSWORD2,
                    'identity': NOIDENTITY,
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
            m.assert_called_with(NAME1, via=None, extras='')

    def test_forward(self):
        rc = sshx.invoke(['forward', NAME1])
        self.assertEqual(c.STATUS_FAIL, rc)

        FORWARD1 = ':8000:127.0.0.1:8000'
        RFORWARD1 = '127.0.0.1:9000:127.0.0.1:9000'
        with mock.patch('sshx.sshx.handle_forward') as m:
            sshx.invoke(['forward', NAME1, '-L', FORWARD1])
            m.assert_called_with(NAME1, background=False,
                                 maps=(FORWARD1,), rmaps=(), via=None)

            sshx.invoke(['forward', NAME1, '-R', RFORWARD1])
            m.assert_called_with(NAME1, background=False,
                                 maps=(), rmaps=(RFORWARD1,), via=None)

            sshx.invoke(['forward', NAME1, '-L', FORWARD1, '-R', RFORWARD1])
            m.assert_called_with(NAME1, background=False, maps=(
                FORWARD1,), rmaps=(RFORWARD1,), via=None)

            sshx.invoke(['forward', NAME1, '-L', FORWARD1, '-b'])
            m.assert_called_with(NAME1, background=True,
                                 maps=(FORWARD1,), rmaps=(), via=None)

    def test_socks(self):
        with mock.patch('sshx.sshx.handle_socks') as m:
            sshx.invoke(['socks', NAME1])
            m.assert_called_with(
                NAME1, via=None, bind='127.0.0.1:1080', background=False)

            sshx.invoke(['socks', NAME1, '-p', 1081])
            m.assert_called_with(NAME1, via=None, bind=1081, background=False)

            sshx.invoke(['socks', NAME1, '-b'])
            m.assert_called_with(
                NAME1, via=None, bind='127.0.0.1:1080', background=True)

            sshx.invoke(['socks', NAME1, '--bind', '0.0.0.0:1080'])
            m.assert_called_with(
                NAME1, via=None, bind='0.0.0.0:1080', background=False)

    def test_scp(self):
        with mock.patch('sshx.sshx.handle_scp') as m:
            sshx.invoke(['scp', 'SRC', 'DST'])
            m.assert_called_with('SRC', 'DST', via=None)

    def test_exec(self):
        with mock.patch('sshx.sshx.handle_exec') as m:
            sshx.invoke(['exec', NAME1, '--tty', '--', 'ls', '-al'])
            m.assert_called_with(NAME1, via=None, tty=True, cmd=('ls', '-al'))

    def test_copyid(self):
        with mock.patch('sshx.sshx.handle_copyid') as m:
            sshx.invoke(['copyid', IDENTITY2, NAME1, '-v', NAME2])
            m.assert_called_with(NAME1, IDENTITY2, via=NAME2)


global_test_init()

if __name__ == '__main__':
    unittest.main()
