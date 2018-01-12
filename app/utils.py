# coding=utf-8

from hashlib import sha256

def hash_sha256(text):
    hash_new = sha256()
    hash_new.update(text.encode('utf-8'))
    return hash_new.hexdigest()