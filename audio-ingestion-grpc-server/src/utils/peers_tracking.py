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

import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join("..", "config")))
import utils.logger as config

log = config.get_logger()


class PeerSet(object):
    def __init__(self):
        self._peers_lock = threading.RLock()
        self._peers = {}

    def connect(self, peer):
        log.debug("Peer {} connecting".format(peer))
        with self._peers_lock:
            if peer not in self._peers:
                self._peers[peer] = 1
            else:
                self._peers[peer] += 1

    def disconnect(self, peer):
        log.debug("Peer {} disconnecting".format(peer))
        with self._peers_lock:
            if peer not in self._peers:
                raise RuntimeError(
                    "Tried to disconnect peer '{}' but it was never connected.".format(
                        peer
                    )
                )
            self._peers[peer] -= 1
            if self._peers[peer] == 0:
                del self._peers[peer]

    def peers(self):
        with self._peers_lock:
            return self._peers.keys()
