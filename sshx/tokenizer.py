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

def hash(s):
    sha1 = hashlib.sha1()
    sha1.update(bytearray(s, 'utf-8'))
    return sha1.hexdigest()
