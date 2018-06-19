from __future__ import unicode_literals


def account_filter(accounts):
    d = {}
    for account in accounts:
        d[account['name']] = account
    l = d.values()
    accounts.clear()
    accounts.extend(l)


def find_by_name(accounts, name):
    for a in accounts:
        if a['name'] == name:
            return a


def add_or_update(accounts, account):
    origin = find_by_name(accounts, account['name'])
    if origin:
        origin.update(account)
    else:
        accounts.append(account)
