"""
 Copyright (C) 2021 Intel Corporation
 SPDX-License-Identifier: BSD-3-Clause
"""

import sounddevice as sd
import soundfile as sf

print("Available Devices : \n{}".format(sd.query_devices()))

print("Default Device ID : {}".format(sd.default.device[0]))


filename = 'audio.wav'
# Extract data and sampling rate from file
data, fs = sf.read(filename, dtype='float32')  
sd.play(data, fs)
status = sd.wait()  # Wait until file is done playing