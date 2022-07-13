
# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause

FROM ubuntu:18.04 as build

# CMake and C compiler 
RUN apt update && apt install -y \
    build-essential \
    git \
    make \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/*

USER root

RUN apt update && apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt install python3.8 -y
RUN wget https://cmake.org/files/v3.15/cmake-3.15.0-Linux-x86_64.sh \
    && mkdir /opt/cmake \
    && chmod +x ./cmake-3.15.0-Linux-x86_64.sh\
    && ./cmake-3.15.0-Linux-x86_64.sh --prefix=/opt/cmake --skip-license

RUN update-alternatives --install /usr/bin/cmake cmake /opt/cmake/bin/cmake 1 --force

# Clone EII C Utils
WORKDIR /eii
RUN git clone --branch release/v2.6.1 --depth=1 https://github.com/open-edge-insights/eii-c-utils

# Build and Install IntelSafeString
WORKDIR /eii/eii-c-utils/IntelSafeString/build
ENV CMAKE_INSTALL_PREFIX="/opt/intel/eii"
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/intel/eii/lib/
RUN cmake -DCMAKE_INSTALL_INCLUDEDIR=$CMAKE_INSTALL_PREFIX/include -DCMAKE_INSTALL_PREFIX=$CMAKE_INSTALL_PREFIX .. && make && make install

# Build and Install EII C Utils
WORKDIR /eii/eii-c-utils
RUN ./install.sh

WORKDIR /eii/eii-c-utils/build
RUN cmake -DCMAKE_INSTALL_INCLUDEDIR=$CMAKE_INSTALL_PREFIX/include -DCMAKE_INSTALL_PREFIX=$CMAKE_INSTALL_PREFIX .. && make && make install

# Build and Install EII Message Bus
RUN apt install  -y
WORKDIR /eii
RUN git clone --branch release/v2.6.1 --depth=1 https://github.com/open-edge-insights/eii-messagebus
WORKDIR /eii/eii-messagebus
RUN ./install.sh --cython

WORKDIR /eii/eii-messagebus/build

RUN cmake -DCMAKE_INSTALL_INCLUDEDIR=$CMAKE_INSTALL_PREFIX/include -DCMAKE_INSTALL_PREFIX=$CMAKE_INSTALL_PREFIX -DWITH_PYTHON=ON .. && make && make install

# Setup EII Message Bus Python bindings
WORKDIR /eii/eii-messagebus/python

RUN python3.8 -m pip install Cython
RUN apt-get install python3.8-dev -y
RUN python3.8 setup.py install

# Cleanup all EII Setup
RUN rm -rf /eii
WORKDIR /

## Text Ingestion Module
FROM build

WORKDIR /app

# RUN python3.8 -m pip install numpy
# RUN python3.8 -m pip install --upgrade pip
# RUN python3.8 -m pip install scipy==1.8.1

HEALTHCHECK NONE


# RUN python3.8 -m pip install grpcio
# RUN python3.8 -m pip install grpcio-tools
# important part, to avoid _portaudio import module not found.

RUN apt-get update
RUN apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 -y
RUN apt-get install python3.8 python3.8-dev python3-pip -y
RUN apt-get install -y portaudio19-dev
RUN python3.8 -m pip install pyaudio==0.2.11
#

RUN apt install -y swig \
    portaudio19-dev \
    libpulse-dev \
    libportaudiocpp0 \
    libasound2-dev \
    python3-pyaudio \
    libasound2 \
    libportaudio2 \
    libasound-dev \
    alsa-utils \
    alsa-base \
    libsndfile1 \
    libglib2.0-0 \
    pulseaudio 

# RUN python3.8 -m pip install respeaker \
# webrtcvad \
# pocketsphinx \
# grpcio \
# protobuf
COPY requirements.txt requirements.txt
RUN python3.8 -m pip install --upgrade pip

RUN python3.8 -m pip install -r requirements.txt
COPY protos /app/protos

RUN python3.8 -m grpc_tools.protoc -I /app/protos/ --python_out=/app --grpc_python_out=/app audio_ingestion.proto
RUN python3.8 -m grpc_tools.protoc -I  /app/protos/ --python_out=/app --grpc_python_out=/app asr.proto
# CMD python3.8 -c "import pyaudio"



# RUN python3.8 -m pip install PyAudio


# # RUN python3.8 -m pip install webrtcvad
# # RUN python3.8 -m pip install pocketsphinx
# # RUN python3.8 -m pip install grpcio
# # RUN python3.8 -m pip install protobuf
# #RUN python3.8 -m pip install grpc
COPY audio_files /app/audio_files
COPY audio_ingestion.py /app
# #CMD python3.8 -c "import time; time.sleep(1000000000)"
CMD python3.8 audio_ingestion.py