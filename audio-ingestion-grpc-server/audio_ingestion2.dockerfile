# INTEL CONFIDENTIAL
# Copyright (C) 2022 Intel Corporation
# This software and the related documents are Intel copyrighted materials, 
# and your use of them is governed by the express license under which they 
# were provided to you ("License"). Unless the License provides otherwise, 
# you may not use, modify, copy, publish, distribute, disclose or transmit 
# this software or the related documents without Intel's prior written permission.
# This software and the related documents are provided as is, with no express 
# or implied warranties, other than those that are expressly stated in the License.

FROM ubuntu:20.04

LABEL description="Audio Ingestion Image"
LABEL vendor="Intel Corporation"

USER root
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
    && apt-get install -y python3 \
                       python3-pip \
                       swig \
                       libpulse-dev \
                       libasound2-dev \
                       python3-pyaudio \
                       libasound2 \
                       libportaudio2 \
                       libasound-dev \
                       alsa-utils \
                       alsa-base \
                       libsndfile1 \
                       libglib2.0-0 \
                       pulseaudio \
    && python3 -m pip install --upgrade pip \
    && mkdir -p /home/audio_ingestion/server_certificates/

COPY protos /home/audio_ingestion/protos
COPY services/src /home/audio_ingestion/src

COPY services/requirements.txt /home/audio_ingestion/

WORKDIR /home/audio_ingestion

RUN pip3 install -r /home/audio_ingestion/requirements.txt \
    && python3 -m grpc_tools.protoc -I ./protos/ --python_out=./src/ --grpc_python_out=./src/ audio_ingestion.proto

CMD python3 src/server.py
