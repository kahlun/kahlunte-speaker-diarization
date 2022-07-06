"""
 Copyright (C) 2021 Intel Corporation
 SPDX-License-Identifier: BSD-3-Clause
"""
from __future__ import print_function

# from concurrent.futures import thread

"""The Python implementation of the announcement bot."""

import logging
import grpc
import tts_pb2
import tts_pb2_grpc
import os
import numpy
import threading, queue
import sounddevice as sd
import eii.msgbus as mb

import signal

import sys

sys.path.append(os.path.abspath(os.path.join("..", "config")))

import logger as config

log = config.get_logger()
log.debug("Path: {}".format(os.path.abspath(os.path.join("..", "config"))))


class TtsMessageQueue:
    def __init__(self):
        self.q = queue.Queue()

    def put(self, item):
        self.q.put(item)

    def get(self):
        return self.q.get(block=True, timeout=None)

    def task_done(self):
        self.q.task_done()

    def join(self):
        self.q.join()


# Message Queue for the {Key, Value} pair. Value will have the text data
MQ = TtsMessageQueue()
# Playback Queue for the audio_data. This will have audio data to be played.
PBQ = TtsMessageQueue()


def bot_zeroMQ_collector():
    """This is the producer thread.
    It will produce text data for the intel's tts engine."""
    msgbus = None
    subscriber = None

    try:
        zmq_topic = (
            os.environ.get("ZMQ_TOPIC")
            if os.environ.get("ZMQ_TOPIC") != None
            else "tts_zmq_topic"
        )

        mb_config = {
            "type": os.environ.get("ZMQ_TYPE")
            if os.environ.get("ZMQ_TYPE") != None
            else "zmq_tcp",
            zmq_topic: {
                "host": os.environ.get("ZMQ_HOST_IP")
                if os.environ.get("ZMQ_HOST_IP") != None
                else "127.0.0.1",
                "port": int(
                    os.environ.get("ZMQ_HOST_PORT")
                    if os.environ.get("ZMQ_HOST_PORT") != None
                    else 3000
                ),
            },
        }
        log.debug(mb_config)

        log.debug("Collector Thread")
        log.debug("Initializing message bus context")
        msgbus = mb.MsgbusContext(mb_config)

        log.debug(f"Initializing subscriber for topic '{zmq_topic}'")
        subscriber = msgbus.new_subscriber(zmq_topic)

        while True:
            # Receive from EII MB, post the text data to tts Message Queue.
            msg = subscriber.recv()
            msg = msg.get_meta_data()

            MQ.put(msg)
            # Block until all tasks are done.
            # This acts as kind of ACK.
            # Comment below to make it unblocking and continously process the Q.
            if block_input == "True" or block_input == "T":
                MQ.join()
                # ACK for audio playback processed
                PBQ.join()
    except Exception as msg:
        log.error("Received Exception: {}".format(msg))
    finally:
        if subscriber is not None:
            subscriber.close()


def bot_tts_client_engine():
    """This is the consumer thread.
    It will consume the text data produced by zeroMQ collector."""
    try:
        with grpc.insecure_channel(tts_server_endpoint, options=(('grpc.enable_http_proxy', 0),)) as channel:
            log.debug(tts_server_endpoint)
            log.debug("tts_server_endpoint")
            ttsstub = tts_pb2_grpc.TtsStub(channel)
            log.debug("TTS Client Engine Thread")
            while True:
                # Get item from the queue. Thread wait on item arrival.
                item = MQ.get()

                # Prepare the request message
                log.debug("Preparing Request Message")
                tts_req = tts_pb2.TextToSpeechRequest()
                for key, value in item.items():
                    tts_req.text_data = value
                    tts_req.tts_model = int(key[2])

                    # Below depends on the model type
                    tts_req.speaker_id = (
                        int(os.environ.get("speaker_id"))
                        if os.environ.get("speaker_id") != None
                        else 19
                    )
                    tts_req.device = (
                        str(os.environ.get("device"))
                        if os.environ.get("device") != None
                        else "CPU"
                    )
                    tts_req.alpha = (
                        float(os.environ.get("alpha"))
                        if os.environ.get("alpha") != None
                        else 1.0
                    )
                    tts_req.cache = (
                        bool(os.environ.get("cache"))
                        if os.environ.get("cache") != None
                        else 0
                    )

                    # AI inference call with the request.
                    log.info(ttsstub.TextToSpeech)
                    response = ttsstub.TextToSpeech(tts_req)

                    log.debug("Text to speech latency: %f", response.inference_time)
                    log.debug("Putting Audio Data to Playback Queue")
                    # Put the audio data to a play back queue
                    PBQ.put(response.audio_output)

                    # Inference done.
                    # log.info("Inference done. Inference time taken : ", response.inference_time)

                    # ACK
                MQ.task_done()
    except Exception as msg:
        log.error("Received Exception: {}".format(msg))


def playback_audio_data():
    # This a playback thread used to play the auido data received
    try:
        log.debug("Audio Playback Thread")
        while True:
            audio_data = PBQ.get()
            log.debug("Creating Output Audio Data file")
            # Form in memory audio data file from the received audio output.
            # Convert the recieved binary audio data into numpyt array
            audio_file = numpy.frombuffer(audio_data, dtype=numpy.int16)

            # Set the playback device to what is provided by user or default device
            sd.default.device = (
                int(os.environ.get("default_device"))
                if os.environ.get("default_device") != None
                else sd.default.device
            )

            log.debug("Playing Audio")
            # Play the audio on the targeted device
            samplerate = (
                int(os.environ.get("samplerate"))
                if os.environ.get("samplerate") != None
                else 22050
            )
            sd.play(audio_file, samplerate)
            # Wait until the audio file is fully played
            sd.wait()

            # ACK
            PBQ.task_done()
    except Exception as msg:
        log.error("Received Exception: {}".format(msg))
        log.info("Check if the inputs provided are valid")


def signal_handler(sig, frame):
    # On Ctrl+C kill the process
    os.kill(os.getpid(), signal.SIGTERM)


if __name__ == "__main__":
    tts_server_endpoint = os.environ.get("tts_server_endpoint") or "localhost:50052"
    logging.basicConfig()
    log.info(tts_server_endpoint)

    # Print out all the input and output audio devices
    log.info("\nAvailable devices : \n{}".format(sd.query_devices()))

    # ASYNC vs SYNC switch.
    # Set it 'T' to block text input in Message Queue - MQ (Use this as ACK) until audio playback is complete.
    block_input = os.environ.get("block_input") or "False"

    # print out all the input and output audio devices
    log.info("\nAvailable devices : \n{}".format(sd.query_devices()))

    # Thread 1 : bot_zeroMQ_collector : text data producer thread for the tts client engine
    t1 = threading.Thread(target=bot_zeroMQ_collector)

    # Thread 2 : bot_tts_client_engine : text data consumer thread and producer of audio data
    t2 = threading.Thread(target=bot_tts_client_engine)

    # Thread 3 : playback_audio_data : audio playback thread
    t3 = threading.Thread(target=playback_audio_data)

    # first start the tts engine thread.
    t2.start()
    # next start the zmq collector thread.
    t1.start()
    # last the playback thread.
    t3.start()

    if os.environ.get("INSIDE_DOCKER") != "True":
        signal.signal(signal.SIGINT, signal_handler)
        while True:
            # Don't exit main, so that it can process any key from the user
            block_input = input()
