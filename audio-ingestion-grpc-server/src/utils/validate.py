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

import cache.audio_ingestion_cache as cache
import utils.logger as config
import pyaudio

log = config.get_logger()

"""
This function checks 
1. If the device is available in the cache
2. If the device selected by the user is available and attached to the system
3. If the device is available for use
"""


def validate_device(audio_device):
    pyaudio_instance = pyaudio.PyAudio()
    total_device_count = pyaudio_instance.get_device_count()
    for dev in range(total_device_count):
        if audio_device == pyaudio_instance.get_device_info_by_index(dev)["name"]:
            log.info("{} connected to system. Verified".format(audio_device))
            return True
    log.error("{} device not available".format(audio_device))
    return False


def validate_input(audio_device):
    log.info("Initiating validation...")
    if validate_device(audio_device) == False:
        return False
    cache_state = cache.cache_obj.ifcached(audio_device)
    log.debug("Cache Status :: {}".format(cache_state))
    if cache_state != True:
        log.warning("Mic not cached earlier")
        return True
    log.debug("Mic cache available. Checking for thread status")
    cache_item = cache.cache_obj.getcached(audio_device)
    log.debug("Thread Status Activity : {}".format(cache_item["thread_obj"].is_alive()))
    if cache_item["thread_obj"].is_alive():
        return False
    return True
