import sys
from pyllist import dllist, dllistnode


class Caching:
    def __init__(self):
        self.dictionary = {}
        self.linked_list = dllist()
        self.max_size = 50000000
        self.size = 0

    def ifcached(self, key):
        if key in self.dictionary:
            return True
        else:
            return False

    def getcached(self, key):
        pointer = self.linked_list.remove(self.dictionary[key])
        self.dictionary[key] = self.linked_list.append(pointer)
        return pointer[1]

    def remove_least_recently_used(self):
        pointer = self.linked_list.remove(self.linked_list.first)
        self.size -= sys.getsizeof(pointer[1])
        self.dictionary.pop(pointer[0])
        return

    def cache(self, key, value):
        if self.max_size <= self.size:
            self.remove_least_recently_used()

        pointer = self.linked_list.append((key, value))
        self.dictionary[key] = pointer
        self.size += sys.getsizeof(value)

    def clear_cache(self):
        while self.linked_list.last != None:
            self.linked_list.pop()
        self.dictionary.clear()
        self.size = 0
        return "Cache Cleared"

    def set_max_cache_size(self, size):
        self.max_size = size
        return
