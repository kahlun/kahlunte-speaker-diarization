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

from concurrent import futures
from audio_ingestion import AudioIngestion
import grpc
import utils.logger as config
import audio_ingestion_pb2_grpc
import utils._configs as cfg

log = config.get_logger()
cfg.run_mode = 'wav'# additional

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        audio_ingestion_pb2_grpc.add_AudioIngestionServicer_to_server(
            AudioIngestion(), server
        )
        if cfg.envi.lower() == "dev":
            log.info("Recognized to be DEV Environment")
            server.add_insecure_port("[::]:" + str(cfg.PORT))
        else:
            log.info("Recognized to be PROD Environment")
            private_key = open(cfg.AUD_SERVER_KEY, "rb").read()
            certificate_chain = open(cfg.AUD_SERVER_CERT, "rb").read()
            ca_cert = open(cfg.AUD_SERVER_CA, "rb").read()
            log.debug("Certificate Files Read")
            credentials = grpc.ssl_server_credentials(
                [(private_key, certificate_chain)],
                root_certificates=ca_cert,
                require_client_auth=True,
            )
            server.add_secure_port("[::]:" + str(cfg.PORT), credentials)
            log.debug("Updated Server Credentials")
        log.info("Run mode identified to be {} ".format(cfg.run_mode))
        log.info("Starting Server on port {}".format(str(cfg.PORT)))
        server.start()
        server.wait_for_termination()
    except Exception as msg:
        log.error("Received Excepton :{}".format(msg))
        exit()


if __name__ == "__main__":
    serve()
