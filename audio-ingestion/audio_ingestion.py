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

import grpc
import audio_ingestion_pb2
import audio_ingestion_pb2_grpc
import grpc
from scipy.io.wavfile import read, write
import io
import os
import sys
import json
import logging
import pyaudio

# sys.path.append(os.path.abspath(os.path.join("..", "config")))
# import logger as config

# log = config.get_logger() # no want grpc that module
LOGGING_LEVEL = (
    os.environ.get("LOGGING_LEVEL")
    if os.environ.get("LOGGING_LEVEL") != None
    else 20 # 20 # info # 10 #debug
)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s] - %(message)s",
    level=LOGGING_LEVEL,
)
logging.root.setLevel(LOGGING_LEVEL)
log = logging.getLogger()
log.setLevel(LOGGING_LEVEL)

# part of lun's audio ingestion EII library
import eii.msgbus as mb
import base64
from scipy.io import wavfile 
import time
import hashlib
import numpy as np

WAV_FILE = "audio.wav"
WAV_FILE = os.environ.get("AUDIO_FILE_PATH") or 'original-vistry-ffmpeg-1-minute.wav'

# WAV_FILE = "how_are_you_doing.wav"
# AUD_HOST = "localhost:50054"
# AUD_HOST = "localhost:50054"
AUD_HOST = "127.0.0.1:50054"
AUD_CERT = "client_certificates/client.crt"
AUD_KEY = "client_certificates/client.key"
AUD_CA = "client_certificates/ca.crt"
ENV_TYPE = "dev"
SAMPLING_RATE = 16000
SAMPLE_WIDTH = 2
CHANNEL_NUM = 1
COMPRESSION_TYPE = "NONE"
WAKE_WORD = "respeaker"
MAX_RECORD_TIME = 10
VAD_TIMEOUT = 3

class EII_MB:
    def __init__(self) -> None:
        self.configuration = {
            "type": os.environ.get("ZMQ_TYPE") or "zmq_tcp",
            "zmq_tcp_publish": {
                "host": os.environ.get("ZMQ_HOST_IP") or "127.0.0.1",
                "port": int(os.environ.get("ZMQ_HOST_PORT")) or 3000,
            },
        }

    def get_config(self):
        return self.configuration


def run():
    # try:
    #     if envi.lower() == ENV_TYPE:
    #         channel = grpc.insecure_channel(audio_ingestion_host)
    #         log.info("Recognized to be DEV Environment")
    #     else:
    #         log.info("Recognized to be PROD Environment")
    #         cert = open(AUD_CERT, "rb").read()
    #         key = open(AUD_KEY, "rb").read()
    #         ca_cert = open(AUD_CA, "rb").read()
    #         credentials = grpc.ssl_channel_credentials(ca_cert, key, cert)
    #         log.debug("Updated the Client Credentials")
    #         channel = grpc.secure_channel(
    #             target=audio_ingestion_host, credentials=credentials
    #         )
    #     log.info("Connecting to server...")
    #     stub = audio_ingestion_pb2_grpc.AudioIngestionStub(channel)
    #     req = audio_ingestion_pb2.BatchIngestRequest()
    #     req.sampling_rate = sampling_rate
    #     req.sample_width = sample_width
    #     req.channel_num = channel_num
    #     req.compression_type = compression_type
    #     req.audio_device_name = audio_device_name
    #     req.wake_word = wake_word
    #     req.notifier_status = notifier_status
    #     req.max_record_time = max_record_time
    #     req.vad_timeout = vad_timeout
    #     log.info("Req parameters :: {}".format(req))
    #     response = stub.AudioIngestBatchInit(req)
    #     for i in response:
    #         log.info(
    #             "Message Type :: {}".format(
    #                 audio_ingestion_pb2.AudioIngestResponse.MessageType.Name(i.msg_type)
    #             )
    #         )
    #         if (
    #             audio_ingestion_pb2.AudioIngestResponse.MessageType.Name(i.msg_type)
    #             == "audio"
    #         ):

                ## handler received audio                
                # rate, data = read(io.BytesIO(i.msg_audio)) # will use in client eii audio ingestion part
                # write(WAV_FILE, rate, data)
                # import time; 
                # time.sleep(1000000000)
                # logging.info("Data written onto {}".format(WAV_FILE))
                
                # implement eii audio ingestion
                # level = logging.DEBUG
                # logging.basicConfig(
                #     format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s] - %(message)s",
                #     level=level,
                # )
                # logging.root.setLevel(level)
                # log = logging.getLogger()
                # log.setLevel(level)

                msgbus = None
                publisher = None

                topic = os.environ.get("ZMQ_TOPIC") or "audio_for_speaker_diarization"
                # topic = "audio_for_speaker_diarization"
                # audio_file_path = 'original-vistry-ffmpeg-1-minute.wav'
                audio_file_path = 'audio_files/' + WAV_FILE
                # interval = 10
                interval = int(os.environ.get("PUBLISH_INTERVAL")) or 10
                # audio_file_path = os.environ.get("AUDIO_FILE_PATH") or 'original-vistry-ffmpeg-1-minute.wav'

                log.debug("Initializing EII Message Bus Configuration")
                mb_config = EII_MB().get_config()

                log.debug(f'ZMQ Type = \'{mb_config["type"]}\'')
                log.debug(f'ZMQ Host IP = {mb_config["zmq_tcp_publish"]["host"]}')
                log.debug(f'ZMQ Host Port = {mb_config["zmq_tcp_publish"]["port"]}')
                # log.debug(f"Interval between each publish = {interval} seconds")

                log.debug("Initializing message bus context")
                msgbus = mb.MsgbusContext(mb_config)

                log.debug(f"Initializing publisher for topic '{topic}'")
                publisher = msgbus.new_publisher(topic)

                log.info("Running...")
                try:

                    sampling_rate_eii, data = read('audio_files/' + WAV_FILE)
                    log.info("found wav file ...")
                    
                    # sampling_rate_eii, data = read(wav)
                    # log.info(type(data))
                    # log.info('type(data)')
                    # log.info(data.dtype)
                    to_send_base64 =  base64.b64encode(data)
                    hash = hashlib.sha1()
                    hash.update(str(time.time()).encode('utf-8'))
                    unique_key = hash.hexdigest()
                    
                    meta = {
                        'sampling_rate' : sampling_rate,
                        'last' : False,
                        'id' : unique_key,
                    }
                    total = 0
                    log.info("Publishing the audio file")
                    MAX_MB = 1024 * 1024 * 61
                    # MAX_MB = 66961920 #tested largest file after convert base64
                    chunks_length = int(len(to_send_base64) / MAX_MB)
                    
                    # though size limit issue, because 50mb, 50,221,542 bytes file fail, but < 5mb file pass without sleep.
                    # this is the solution with chunk size + sleep, if send multiple chunk without sleep will fail too.
                    # def send_with_chunks(to_send_base64, meta):
                    #     if(chunks_length is not 0): #no need chunk

                    #         chunks, chunk_size = len(to_send_base64), int(len(to_send_base64)/chunks_length)
                    #         to_send_list = [to_send_base64[i:i+chunk_size] for i in range (0, chunks, chunk_size)]

                    #         for x in to_send_list:
                    #             print('pushed')
                    #             total+= len(x)
                    #             if(x != to_send_list[-1]):
                    #                 print('one chunk')
                    #                 publisher.publish((meta, x))
                    #             else:
                    #                 print('last piece')
                    #                 meta['last'] = True
                    #                 publisher.publish((meta, x))
                    #             time.sleep(0.1) # very important to sleep after assume it is published.
                    #     else:
                    #         publisher.publish((meta, to_send_base64))
                    #         time.sleep(0.1) # very important to sleep after assume it is published.

                    meta['last'] = True
                    meta['dtype'] = str(data.dtype)
                    r = base64.decodebytes(to_send_base64)
                    response_as_np_array = np.frombuffer(r, dtype=np.dtype(getattr(np, str(data.dtype))))
                    # wavfile.write('temp_debug_.wav', 16000, response_as_np_array)
                    # time.sleep(1000000000)
                    # logging.info("Data written onto {}".format(WAV_FILE))
                    publisher.publish((meta, to_send_base64))
                    # publisher.publish((meta, data))
                    time.sleep(0.1) # very important to sleep after assume it is published.

                    log.info("Published...")

                except KeyboardInterrupt:
                    log.debug("Quitting...")
                finally:
                    if publisher is not None:
                        publisher.close()
                
            # else:
            #     log.info(
            #         "Message Control: {}".format(
            #             audio_ingestion_pb2.AudioIngestResponse.MessageControl.Name(
            #                 i.msg_control
            #             )
            #         )
            #     )
            #     log.info("Device Name: {}".format(i.audio_device))
            # break
    # except Exception as e:
    #     log.error("Received Exception: {}".format(e))

    # print('end of audio ingestion client handler.')

if __name__ == "__main__":
    # logging.basicConfig()

    # pyaudio_instance = pyaudio.PyAudio()
    # default_device = pyaudio_instance.get_default_input_device_info()

    audio_ingestion_host = (
        os.environ.get("audio_ingestion_host")
        if os.environ.get("audio_ingestion_host") != None
        else AUD_HOST
    )
    envi = str(os.environ.get("env")) if os.environ.get("env") != None else ENV_TYPE

    sampling_rate = (
        int(os.environ.get("sampling_rate"))
        if os.environ.get("sampling_rate") != None
        else SAMPLING_RATE
    )

    sample_width = (
        int(os.environ.get("sample_width"))
        if os.environ.get("sample_width") != None
        else SAMPLE_WIDTH
    )

    channel_num = (
        int(os.environ.get("channel_num"))
        if os.environ.get("channel_num") != None
        else CHANNEL_NUM
    )

    compression_type = (
        str(os.environ.get("compression_type"))
        if os.environ.get("compression_type") != None
        else COMPRESSION_TYPE
    )

    # audio_device_name = (
    #     str(os.environ.get("audio_device_name"))
    #     if os.environ.get("audio_device_name") != None
    #     else default_device["name"]
    # )

    wake_word = (
        str(os.environ.get("wake_word"))
        if os.environ.get("wake_word") != None
        else WAKE_WORD
    )

    notifier_status = (
        bool(os.environ.get("notifier_status"))
        if os.environ.get("notifier_status") != None
        else False
    )

    max_record_time = (
        int(os.environ.get("max_record_time"))
        if os.environ.get("max_record_time") != None
        else MAX_RECORD_TIME
    )

    vad_timeout = (
        int(os.environ.get("vad_timeout"))
        if os.environ.get("vad_timeout") != None
        else VAD_TIMEOUT
    )

    run()