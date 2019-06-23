from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

import hashlib
from itsdangerous import URLSafeSerializer, SignatureExpired, BadData

def _salt(s):
    m = hashlib.md5()
    m.update(s.encode('utf-8'))
    return m.hexdigest()

def encrypt(string, key):
    salt = _salt(key)
    s = URLSafeSerializer(key)
    return s.dumps(string, salt)

def decrypt(token, key):
    salt = _salt(key)    
    s = URLSafeSerializer(key)
    return s.loads(token, salt=salt)