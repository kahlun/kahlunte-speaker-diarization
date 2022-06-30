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


def create_json_response(audio_device, msg_type, msg_audio, msg_control):
    return {
        "audio_device": audio_device,
        "msg_type": msg_type,
        "msg_audio": msg_audio,
        "msg_control": msg_control,
    }
