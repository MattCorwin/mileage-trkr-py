import hashlib
import random
import string

def make_salt():
    return ''.join([random.choice(string.ascii_letters) for x in range (5)])
def make_pw_hash(password, salt=None, pepper=None):
    if not salt:
        salt = make_salt()
    if not pepper:
        pepper = random.choice(string.ascii_letters)
    hash = hashlib.sha256(str.encode(password + salt + pepper)).hexdigest()
    return '{0},{1}'.format(hash,salt)

def check_pw_hash(password, hash):
    salt = hash.split(',')[1]
    for letter in string.ascii_letters:
        if make_pw_hash(password, salt, letter) == hash:
            return True
    
    return False