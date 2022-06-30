"""
INTEL CONFIDENTIAL
Copyright (C) 2022 Intel Corporation
This software and the related documents are Intel copyrighted materials, 
and your use of them is governed by the express license under which they 
were provided to you ("License"). Unless the License provides otherwise, 
you may not use, modify, copy, publish, distribute, disclose or transmit 
this software or the related documents without Intel's prior written permission.
This software and the related documents are provided as is, with no express 
or implied warranties, other than those that are expressly stated in the License.
"""


class Singleton(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, "_instance"):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


class Caching(Singleton):
    def __init__(self):
        self.dictionary = {}

    def ifcached(self, key):
        if key in self.dictionary:
            return True
        else:
            return False

    def getcached(self, key):
        return self.dictionary[key]

    def get_all_cached(self):
        return self.dictionary

    def cache(self, key, value):
        self.dictionary[key] = value


cache_obj = Caching()
