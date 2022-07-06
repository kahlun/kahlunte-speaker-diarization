import hashlib


class Hashing:
    def __init__(self):
        self.digest_size = 10

    def create_hash_key(self, key_list):
        hash_object = hashlib.blake2b(digest_size=self.digest_size)
        for i in key_list:
            hash_object.update(str(i).encode())  # update all the keys in hash object
        hex_dig = hash_object.hexdigest()
        return hex_dig
