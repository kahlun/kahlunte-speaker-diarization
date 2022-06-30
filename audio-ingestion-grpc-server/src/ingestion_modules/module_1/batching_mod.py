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

from respeaker import Microphone
import pyaudio
import io
import wave
import utils._configs as cfg
import utils.logger as config
import ingestion_modules.device_identifier as dev_ident
import utils.create_resp as cr_rp

log = config.get_logger()


def mod_1_batch(quit_event, input_data):
    log.debug("Obtained Input :: {}".format(input_data))
    pyaudio_instance = pyaudio.PyAudio()
    mic = Microphone(pyaudio_instance=pyaudio_instance, quit_event=quit_event)
    notifier_status = False
    default_device = pyaudio_instance.get_default_input_device_info()["name"]
    if "notifierStatus" in input_data:
        notifier_status = bool(input_data["notifierStatus"])
    log.debug("Notifier Status:: {}".format(notifier_status))
    log.debug("Default input device assigned is {}".format(default_device))
    device_details, device_index = dev_ident.identify_device_details(
        pyaudio_instance, input_data["audioDeviceName"]
    )
    mic.device_index = device_index
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
                data = mic.listen(
                    duration=input_data["maxRecordTime"],
                    timeout=input_data["vadTimeout"],
                )
                log.info("Listening...")
                recorded_wav_bytes = io.BytesIO()
                with wave.open(recorded_wav_bytes, "wb") as wav:
                    wav.setsampwidth(input_data["sampleWidth"])
                    wav.setnchannels(input_data["channelNum"])
                    wav.setframerate(input_data["samplingRate"])
                    for d in data:
                        if d:
                            wav.writeframes(d)
                    data = recorded_wav_bytes.getbuffer()
                    input_data["queue"].put(
                        cr_rp.create_json_response(
                            input_data["audioDeviceName"],
                            cfg.AUDIO,
                            data.tobytes(),
                            "audio_data",
                        )
                    )
                if notifier_status:
                    input_data["queue"].put(
                        cr_rp.create_json_response(
                            input_data["audioDeviceName"],
                            cfg.CONTROL,
                            str.encode("Sleep Detected"),
                            cfg.SLEEP,
                        )
                    )
    except Exception as msg:
        log.error("Received Exception {}".format(msg))
        wav.close()
        quit_event.set()
        input_data["queue"].put(
            cr_rp.create_json_response(
                input_data["audioDeviceName"],
                cfg.CONTROL,
                str.encode("Error Occured"),
                cfg.QUIT,
            )
        )
