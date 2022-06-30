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

import logging
import os

LOG_LEVEL = logging.INFO
ENV_TYPE = "dev"
SPEECH_MODE = "speech"
WAV_MODE = "wav"
PORT = 50054

WAKE = "wake"
SLEEP = "sleep"
AUDIO = "audio"
CONTROL = "control"
QUIT = "quit"

audio_server_cert = str(os.environ.get("audio_server_cert")) or "server.crt"
audio_server_key = str(os.environ.get("audio_server_key")) or "server.key"
audio_server_ca = str(os.environ.get("audio_server_ca")) or "ca.crt"

AUD_SERVER_CERT = "server_certificates/" + audio_server_cert
AUD_SERVER_KEY = "server_certificates/" + audio_server_key
AUD_SERVER_CA = "server_certificates/" + audio_server_ca

envi = str(os.environ.get("env")) if os.environ.get("env") != None else ENV_TYPE

run_mode = (
    str(os.environ.get("run_mode"))
    if os.environ.get("run_mode") != None
    else SPEECH_MODE
)

__version__ = "2.0"
