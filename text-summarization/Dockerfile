# Copyright (C) 2021 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause

FROM ubuntu:18.04

# CMake and C compiler 
RUN apt update && apt install -y \
    build-essential \
    git \
    make \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    python3.8-dev 
    
#install python 3.8
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

##end of EII installation

LABEL description="ASR Dialogue image"
LABEL vendor="Intel Corporation"

USER root

ENV INSIDE_DOCKER="True"

RUN mkdir -p /home/speaker-diarization/ \
    && mkdir -p /home/speaker-diarization/double-confirm-data-audio \
    && mkdir -p /home/speaker-diarization/double-confirm-data-audio/ground_truth \
    && mkdir -p /home/speaker-diarization/data \
    # && mkdir -p /home/speaker-diarization/data/audio_files \
    && apt-get update \
    && apt-get install -y python3-pip \
    sox \ 
    libsndfile1

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Singapore

run apt install git-all -y

WORKDIR /home/speaker-diarization/
COPY requirements.txt /home/speaker-diarization/requirements.txt
RUN python3.8 -m pip install --upgrade pip && python3.8 -m pip install -r requirements.txt

COPY double-confirm-data-audio/ground_truth /home/speaker-diarization/double-confirm-data-audio/ground_truth

RUN mkdir -p model/summarization/philschmid/
WORKDIR /home/speaker-diarization/model/summarization/philschmid

RUN apt install git-lfs && git lfs install
RUN git clone https://huggingface.co/philschmid/bart-large-cnn-samsum
RUN pwd



WORKDIR /home/speaker-diarization/

# COPY model /home/speaker-diarization/model
COPY text-summarization.py /home/speaker-diarization/

HEALTHCHECK NONE
#CMD ["python3.8", "-c", "import os;print(os.getcwd());import time;time.sleep(1000000);"]
CMD python3.8 text-summarization.py a