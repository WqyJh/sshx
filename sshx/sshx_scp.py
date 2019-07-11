from sshx import cfg


_SCP_TARGET = '{user}@{host}:{path}'


class Target(object):
    def __init__(self, target):
        r = target.split(':')
        if len(r) == 1:
            self.host, self.path = '', r[0]
        elif len(r) == 2:
            self.host, self.path = r
        else:
            self.host, self.path = None, None

    def is_remote(self):
        return self.host and not self.host in ['localhost', '127.0.0.1']

    def compile(self):
        if self.path is None:
            return ''

        if not self.host:
            return self.path

        if self.host:
            account = cfg.read_account(self.host)
            if account:
                return _SCP_TARGET.format(user=account.user,
                                          host=account.host,
                                          path=self.path)

        return ''


class TargetPair(object):
    def __init__(self, src, dst):
        self.src = Target(src)
        self.dst = Target(dst)

    def both_are_remote(self):
        return self.src.is_remote() and self.dst.is_remote()

