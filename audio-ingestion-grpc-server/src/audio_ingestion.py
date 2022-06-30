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

from google.protobuf.json_format import MessageToDict
import ingestion_modules.mod_selector as mods
import sys
import grpc
import queue
import cache.audio_ingestion_cache as cache
import utils.logger as config
import utils.validate as val
import audio_ingestion_pb2
import audio_ingestion_pb2_grpc
import utils.peers_tracking as peers_tracking
from cleanup import CleanUp
import threading
import utils.create_resp as cr_rp
import utils._configs as cfg

log = config.get_logger()


# class AudioIngestion(audio_ingestion_pb2_grpc.AudioIngestionServicer):
class AudioIngestion():
    def __init__(self):
        self._peer_set = peers_tracking.PeerSet()
        pass

    def _record_peer(self, context, request_dict):
        def _unregister_peer():
            self._peer_set.disconnect(context.peer())
            request_dict["quit_event"].set()
            request_dict["thread_obj"].join(3)
            request_dict["queue"].put(
                cr_rp.create_json_response(
                    request_dict["audioDeviceName"],
                    cfg.CONTROL,
                    str.encode("Closing Connection"),
                    cfg.QUIT,
                )
            )

        context.add_callback(_unregister_peer)
        self._peer_set.connect(context.peer())

    def AudioIngestInit(self, request, context, mod_type):
        log.debug("Audio ingestion Init")
        try:
            request_dict = MessageToDict(request)
            ingestion_module = "module_1"
            if cfg.run_mode != cfg.SPEECH_MODE:
                ingestion_module = "module_2"
                mod_type = "wav"
            if val.validate_input(request.audio_device_name) == False:
                err_msg = "Device unavailable. Something went wrong"
                log.error(err_msg)
                return False, err_msg
            request_dict["queue"] = queue.Queue()
            thread_obj, thread_id, quit_event = mods.module_selector(
                ingestion_module, mod_type, request_dict
            )
            thread_obj.daemon = True
            thread_obj.start()
            request_dict["thread_obj"] = thread_obj
            request_dict["thread_id"] = thread_id
            request_dict["peer_id"] = context.peer()
            request_dict["peer_context"] = context
            request_dict["quit_event"] = quit_event
            self._record_peer(context, request_dict)
            self._clean_up = CleanUp(context)
            log.info("Caching {} ".format(request_dict))
            cache.cache_obj.cache(request.audio_device_name, request_dict)
            return True, request_dict
        except Exception as msg:
            log.error("Received Excepton : {}".format(msg))
            return False, request_dict

    def AudioIngestBatchInit(self, request, context):
        try:
            log.debug("Audio ingestion Batch Init :: {} ".format(context.peer()))
            batch_state, batch_body = self.AudioIngestInit(request, context, "batch")
            if batch_state:
                context.set_code(grpc.StatusCode.OK)
                while True:
                    if batch_body["quit_event"].is_set():
                        break
                    data = batch_body["queue"].get()
                    if "msg_control" in data and data["msg_control"] == "quit":
                        log.debug("Executing Quit")
                        break
                    yield audio_ingestion_pb2.AudioIngestResponse(
                        audio_device=data["audio_device"],
                        msg_type=data["msg_type"],
                        msg_audio=data["msg_audio"],
                        msg_control=data["msg_control"],
                    )
            return audio_ingestion_pb2.AudioIngestResponse(
                audio_device=request.audio_device_name,
                msg_type=cfg.CONTROL,
                msg_audio=str.encode("Closing Connection"),
                msg_control=cfg.QUIT,
            )
        except Exception as msg:
            log.error("Received Excepton : {}".format(msg))
            context.set_details("Something went wrong")
            return audio_ingestion_pb2.AudioIngestResponse(
                audio_device=request.audio_device_name,
                msg_type=cfg.CONTROL,
                msg_audio=str.encode("Error occured"),
                msg_control=cfg.QUIT,
            )

    def AudioIngestStreamInit(self, request, context):
        try:
            log.debug("Audio ingestion Stream Init :: {} ".format(context.peer()))
            stream_state, stream_body = self.AudioIngestInit(request, context, "stream")
            if stream_state:
                log.debug(
                    "Initiating Thread {} from pool".format(threading.current_thread())
                )
                context.set_code(grpc.StatusCode.OK)
                while True:
                    if stream_body["quit_event"].is_set():
                        break
                    data = stream_body["queue"].get()
                    if "msg_control" in data and data["msg_control"] == "quit":
                        log.debug("Executing Quit")
                        break
                    yield audio_ingestion_pb2.AudioIngestResponse(
                        audio_device=data["audio_device"],
                        msg_type=data["msg_type"],
                        msg_audio=data["msg_audio"],
                        msg_control=data["msg_control"],
                    )
            log.info("Returning to Peer")
            return audio_ingestion_pb2.AudioIngestResponse(
                audio_device=request.audio_device_name,
                msg_type=cfg.CONTROL,
                msg_audio=str.encode("Closing Connection"),
                msg_control=cfg.QUIT,
            )
        except Exception as msg:
            log.error("Received Exception : {}".format(msg))
            return audio_ingestion_pb2.AudioIngestResponse(
                audio_device=request.audio_device_name,
                msg_type=cfg.CONTROL,
                msg_audio=str.encode("Error occured"),
                msg_control=cfg.QUIT,
            )
