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

import pyaudio
import io
import time
import numpy as np
import webrtcvad
import utils._configs as cfg
import utils.logger as config
from respeaker import Microphone
import utils.create_resp as cr_rp
import ingestion_modules.device_identifier as dev_ident


log = config.get_logger()


def mod_1_stream(quit_event, input_data):
    log.debug("Obtained Input :: {}".format(input_data))
    pyaudio_instance = pyaudio.PyAudio()
    vad = webrtcvad.Vad(1)
    mic = Microphone(pyaudio_instance=pyaudio_instance, quit_event=quit_event)
    default_device = pyaudio_instance.get_default_input_device_info()["name"]
    log.debug("Default input device assigned is {}".format(default_device))
    device_details, device_index = dev_ident.identify_device_details(
        pyaudio_instance, input_data["audioDeviceName"]
    )
    mic.device_index = device_index
    notifier_status = False
    if "notifierStatus" in input_data:
        notifier_status = bool(input_data["notifierStatus"])
    log.debug("Notifier Status :: {}".format(notifier_status))
    try:
        while not quit_event.is_set():
            if mic.wakeup(input_data["wakeWord"]):
                log.info("Wake up")
                if notifier_status:
                    input_data["queue"].put(
                        cr_rp.create_json_response(
                            input_data["audioDeviceName"],
                            cfg.CONTROL,
                            str.encode("Wake Detected"),
                            cfg.WAKE,
                        )
                    )
                log.info("Listening..."),
                vad_chunks = int(input_data["samplingRate"] / 100)
                chunks = int(input_data["chunkSize"])
                stream = pyaudio_instance.open(
                    input=True,
                    format=pyaudio.paInt16,
                    channels=int(input_data["channelNum"]),
                    rate=int(input_data["samplingRate"]),
                    frames_per_buffer=chunks,
                )
                start_time = time.time()
                for i in range(
                    0,
                    int(
                        input_data["samplingRate"]
                        / chunks
                        * input_data["maxRecordTime"]
                    ),
                ):
                    buffer = stream.read(chunks)
                    vad_buffer = stream.read(vad_chunks)
                    if not vad.is_speech(vad_buffer, input_data["samplingRate"]):
                        end_time = time.time()
                        if (end_time - start_time) >= input_data["vadTimeout"]:
                            log.info("Voice activity not detected")
                            stream.stop_stream()
                            break
                    else:
                        start_time = time.time()
                    np_array = np.frombuffer(buffer, dtype="int16")
                    np_bytes = io.BytesIO()
                    np.save(np_bytes, np_array, allow_pickle=True)
                    input_data["queue"].put(
                        cr_rp.create_json_response(
                            input_data["audioDeviceName"],
                            cfg.AUDIO,
                            np_bytes.getvalue(),
                            "audio_data",
                        )
                    )
                stream.close()
                log.info("Sleep detection notifier Check {}".format(notifier_status))
                if notifier_status:
                    log.info("Sleep detection notified")
                    input_data["queue"].put(
                        cr_rp.create_json_response(
                            input_data["audioDeviceName"],
                            cfg.CONTROL,
                            str.encode("Sleep Detected"),
                            cfg.SLEEP,
                        )
                    )
    except Exception as msg:
        quit_event.set()
        log.error("Received Exception {}".format(msg))
        input_data["queue"].put(
            cr_rp.create_json_response(
                input_data["audioDeviceName"],
                cfg.CONTROL,
                str.encode("Error Occured"),
                cfg.QUIT,
            )
        )
