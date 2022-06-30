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

import io
import wave
import time
import glob
import utils._configs as cfg
import utils.logger as config
import utils.create_resp as cr_rp
from scipy.io.wavfile import read, write

log = config.get_logger()


def wav_ingestion(quit_event, input_data):
    log.debug("Obtained Input :: {}".format(input_data))
    log.info("Initiating wav ingestion")
    try:
        while not quit_event.is_set():
            for file in glob.glob("audio_data_samples/*.wav"):
                time.sleep(3)
                rate, data = read(file)
                recorded_wav = io.BytesIO()
                with wave.open(recorded_wav, "wb") as wav:
                    wav.setsampwidth(2)
                    wav.setnchannels(1)
                    wav.setframerate(16000)
                    for d in data:
                        if d:
                            wav.writeframes(d)
                input_data["queue"].put(
                    cr_rp.create_json_response(
                        input_data["audioDeviceName"],
                        cfg.AUDIO,
                        recorded_wav.getbuffer().tobytes(),
                        "audio_data",
                    )
                )
    except Exception as msg:
        log.error("Received Exception {}".format(msg))
        quit_event.set()
        input_data["queue"].put(
            cr_rp.create_json_response(
                input_data["audioDeviceName"],
                cfg.CONTROL,
                str.encode("Error Occured"),
                cfg.QUIT,
            )
        )
