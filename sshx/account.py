from sshx import utils


DEF_USER = 'root'
DEF_HOST = ''
DEF_PORT = '22'
DEF_PASSWORD = ''
DEF_IDENTITY = ''
DEF_VIA = ''


class Account(object):
    def __init__(self, name, user=DEF_USER, host=DEF_HOST, port=DEF_PORT,
                 password=DEF_PASSWORD, identity=DEF_IDENTITY, via=DEF_VIA):
        self.name = name
        self.user = user
        self.host = host
        self.port = port
        self.password = password
        self.identity = identity
        self.via = via

    def update(self, update):
        if isinstance(update, Account):
            # Trick here. Update self value.
            self.__dict__ = update.__dict__
        else:
            for k, v in update.items():
                setattr(self, k, v)

    def is_valid(self):
        '''
        Return true when all values match utils.is_str().
        '''
        return all(map(utils.is_str, self.__dict__.values()))

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


def find_by_name(accounts, name):
    if name:
        for a in accounts:
            if a.name == name:
                return a


def add_or_update(accounts, account):
    origin = find_by_name(accounts, account.name)
    if origin:
        origin.update(account)
    else:
        accounts.append(account)
