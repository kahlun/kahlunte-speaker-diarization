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
import ingestion_modules.module_1.batching_mod as rp_batch
import ingestion_modules.module_1.streaming_mod as rp_stream
import ingestion_modules.module_2.wav_ingestion as wi
import utils.logger as config

log = config.get_logger()


def module_selector(module, mod_type, input_data):
    log.debug("Module Selected is {}".format(module))
    quit_event = threading.Event()
    mods = {
        "module_1": {
            "batch": threading.Thread(
                target=rp_batch.mod_1_batch,
                args=(
                    quit_event,
                    input_data,
                ),
            ),
            "stream": threading.Thread(
                target=rp_stream.mod_1_stream,
                args=(
                    quit_event,
                    input_data,
                ),
            ),
        },
        "module_2": {
            "wav": threading.Thread(
                target=wi.wav_ingestion,
                args=(
                    quit_event,
                    input_data,
                ),
            ),
        },
    }
    return mods[module][mod_type], threading.get_ident(), quit_event
