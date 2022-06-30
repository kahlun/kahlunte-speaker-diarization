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

import ctypes
import queue
import utils.logger as config
import cache.audio_ingestion_cache as cache

log = config.get_logger()


class CleanUp:
    def __init__(self, context):
        self.context = context

    def kill_thread(self, thread_id):
        log.debug("Killing thread :: {}".format(thread_id))
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            thread_id, ctypes.py_object(SystemExit)
        )
        log.debug("Response :: {}".format(res))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            log.error("Exception raise failure")

    def find_mic_from_context(self):
        cache_data = cache.cache_obj.get_all_cached()
        for peer in cache_data:
            if cache_data[peer]["peer_id"] == self.context.peer():
                return True, cache_data[peer]
        return False, {}

    def empty_queue(self, q):
        log.info("Emptying Queue")
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass

    def clean_up(self):
        mic_state, mic_obj = self.find_mic_from_context()
        if mic_state == False:
            log.error("Unable to find Mic")
            return
        log.debug("Cached Device found : {}".format(mic_obj["audioDeviceName"]))
        self.kill_thread(mic_obj["thread_id"])
        mic_obj["quit_event"].set()
        self.empty_queue(mic_obj["queue"])
        return
