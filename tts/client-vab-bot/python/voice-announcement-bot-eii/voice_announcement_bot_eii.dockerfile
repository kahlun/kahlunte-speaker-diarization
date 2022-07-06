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
RUN python3 setup.py install

# Cleanup all EII Setup
RUN rm -rf /eii
WORKDIR /

## Voice Announcement Bot 
FROM build

LABEL description="Voice announcement bot EII image"
LABEL vendor="Intel Corporation"

USER root

ENV INSIDE_DOCKER="True"
ENV DEBIAN_FRONTEND noninteractive

WORKDIR /home/va-bot/

RUN apt-get update \
    && apt-get install -y python3-pip \
        libasound2 \
        libportaudio2 \
        libasound-dev \
        alsa-utils \
        alsa-base \
        libsndfile1 \
        libglib2.0-0 \
        pulseaudio \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /home/va-bot/
COPY protos /home/va-bot/protos

RUN python3 -m pip install -r requirements.txt \
    && python3 -m grpc_tools.protoc -I /home/va-bot/protos --python_out=/home/va-bot/ --grpc_python_out=/home/va-bot/ tts.proto

COPY config /home/config
COPY voice-announcement-bot.py /home/va-bot/

HEALTHCHECK NONE

CMD python3 voice-announcement-bot.py