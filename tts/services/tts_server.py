"""
 Copyright (C) 2021 Intel Corporation
 SPDX-License-Identifier: BSD-3-Clause
"""

"""The Python implementation of the GRPC helloworld.Greeter server."""

from concurrent import futures
import logging

import grpc
import tts_pb2
import tts_pb2_grpc
import text_to_speech_demo
import os
import time
import io
import wave
import numpy as np
import tts_cache
import hashing
import data_compress_decompress
import logger as config

log = config.get_logger()


class Tts(tts_pb2_grpc.TtsServicer):
    def __init__(self):
        self.caching = True
        self.caching = False if os.environ.get("cache") == "False" else True

    def TextToSpeech(self, request, context):
        """file1 = open("text.txt","w")
        L =  request.text_data
        # \n is placed to indicate EOL (End of Line)
        file1.write(L)
        file1.close()"""
        try:
            log.debug("Calling TTS main")
            if self.caching != True or (
                self.caching == True and request.cache == False
            ):
                log.debug("Caching is disabled, so perform the tts inferencing..")
                response = text_to_speech_demo.tts_main(
                    request.tts_model,
                    request.speaker_id,
                    request.text_data,
                    request.alpha,
                    request.gender,
                    request.style,
                )
                log.debug("Received Audio Response")
                audio = response[0].tobytes()
                log.debug("Converting Audio to Binary Format")
                log.debug("Sending back Response to Client")
                return tts_pb2.TextToSpeechReply(
                    audio_output=audio, inference_time=response[1]
                )
            log.debug("Caching is enabled..")
            key = hash_obj.create_hash_key(
                [
                    request.speaker_id,
                    request.alpha,
                    request.text_data,
                    request.gender,
                    request.style,
                    request.tts_model,
                ]
            )
            if cache_obj.ifcached(key):
                log.debug("Response found in cache.. So return the catched response")
                start = time.time()
                response = cache_obj.getcached(key)
                response = compress_decompress_obj.decompress_data(response)
                log.debug("Sending back Response to Client")
                return tts_pb2.TextToSpeechReply(
                    audio_output=response, inference_time=time.time() - start
                )
            log.debug("Response not found in cache.. So return the inferenced output")
            response = text_to_speech_demo.tts_main(
                request.tts_model,
                request.speaker_id,
                request.text_data,
                request.alpha,
                request.gender,
                request.style,
            )
            log.debug("Received Audio Response")
            audio = response[0].tobytes()
            audio_data = compress_decompress_obj.compress_data(audio)
            log.debug("cache the inferenced output")
            cache_obj.cache(key, audio_data)
            log.debug("Converting Audio to Binary Format")
            log.debug("Sending back Response to Client")
            return tts_pb2.TextToSpeechReply(
                audio_output=audio, inference_time=response[1]
            )
        except Exception as msg:
            log.error("Received Excepton : {}".format(msg))

    def EnableCaching(self, request, context):
        try:
            self.caching = request.enable_caching
            if request.enable_caching == True:
                log.debug("Catching Enabled")
                return tts_pb2.CachingResponse(status="Caching Enabled")
            else:
                log.debug("Catching Disabled")
                return tts_pb2.CachingResponse(status="Caching Disabled")
        except Exception as msg:
            log.error("Received Excepton : {}".format(msg))

    def ClearCache(self, request, context):
        try:
            log.debug(cache_obj.size)
            status = cache_obj.clear_cache()
            log.debug("Cache Cleared")
            log.debug(cache_obj.size)
            return tts_pb2.CachingResponse(status=status)
        except Exception as msg:
            log.error("Received Exception : {}".format(msg))


def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        tts_pb2_grpc.add_TtsServicer_to_server(Tts(), server)
        server.add_insecure_port("[::]:50052")

        log.info("Starting TTS Server")
        server.start()
        server.wait_for_termination()
    except Exception as msg:
        log.error("Received Excepton : {}".format(msg))


if __name__ == "__main__":
    logging.basicConfig()
    f = open("/tmp/health_state.txt", "w")
    f.write("OK")
    f.close()
    cache_obj = tts_cache.Caching()
    hash_obj = hashing.Hashing()
    compress_decompress_obj = data_compress_decompress.Compress_Decompress()
    text_to_speech_demo.load_tts()
    serve()
