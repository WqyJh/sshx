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
        return self.host

    def compile(self, host=''):
        if self.path is None:
            return ''

        if not self.host:
            return self.path

        if self.host:
            account = cfg.read_account(self.host)
            if account:
                if not host:
                    host = account.host
                return _SCP_TARGET.format(user=account.user,
                                          host=host,
                                          path=self.path)

        return ''


    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class TargetPair(object):
    def __init__(self, src, dst):
        self.src = Target(src)
        self.dst = Target(dst)

    def both_are_remote(self):
        return self.src.is_remote() and self.dst.is_remote()
    
    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

