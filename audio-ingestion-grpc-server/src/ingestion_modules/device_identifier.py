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

import utils.logger as config

log = config.get_logger()


def identify_device_details(pyaudio_instance, audio_device_name):
    for dev in range(pyaudio_instance.get_device_count()):
        current_device = pyaudio_instance.get_device_info_by_index(dev)
        if audio_device_name == current_device["name"]:
            log.debug(
                "Using device {} with index {}".format(current_device["name"], dev)
            )
            return current_device, dev
