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
    python3.8-dev \
    apt install software-properties-common -y \
    add-apt-repository ppa:deadsnakes/ppa -y \
    apt install python3.8 -y
    
#install python 3.8
# RUN apt update && apt install software-properties-common -y
# RUN add-apt-repository ppa:deadsnakes/ppa -y
# RUN apt install python3.8 -y

RUN wget https://cmake.org/files/v3.15/cmake-3.15.0-Linux-x86_64.sh \
    && mkdir /opt/cmake \
    && chmod +x ./cmake-3.15.0-Linux-x86_64.sh\
    && ./cmake-3.15.0-Linux-x86_64.sh --prefix=/opt/cmake --skip-license \
    && update-alternatives --install /usr/bin/cmake cmake /opt/cmake/bin/cmake 1 --force
# RUN update-alternatives --install /usr/bin/cmake cmake /opt/cmake/bin/cmake 1 --force

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
RUN python3.8 -m pip install Cython && apt-get install python3.8-dev -y && python3.8 setup.py install
# RUN apt-get install python3.8-dev -y
# RUN python3.8 setup.py install

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
    && mkdir -p /home/speaker-diarization/data/audio_files \
    && apt-get update \
    && apt-get install -y python3-pip \
    sox \ 
    libsndfile1 \
    apt install git-all -y
    # python3.8-dev 

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Singapore

# run apt install git-all -y

WORKDIR /home/speaker-diarization/
COPY requirements.txt /home/speaker-diarization/requirements.txt
RUN python3.8 -m pip install --upgrade pip && python3.8 -m pip install -r requirements.txt
#RUN python3.8 -m pip install packaging
#RUN python3.8 -m pip install setuptools_rust
#RUN python3.8 -m pip install numpy
#RUN python3.8 -m pip install pybind11
#RUN python3.8 -m pip install scipy
RUN python3.8 -m pip install -r requirements.txt
# COPY  data/offline_diarization_with_asr.yaml /home/speaker-diarization/data/offline_diarization_with_asr.yaml

# COPY original-vistry-ffmpeg.wav /home/speaker-diarization

HEALTHCHECK NONE

# server_speaker_diarization_1  | RuntimeError: cannot cache function '__shear_dense': no locator available for file '/usr/local/lib/python3.8/dist-packages/librosa/util/utils.py'
# https://github.com/librosa/librosa/issues/1156

ENV NUMBA_CACHE_DIR=/tmp/NUMBA_CACHE_DIR/
ENV MPLCONFIGDIR=/tmp/MPLCONFIGDIR/
RUN mkdir -m 777 /tmp/NUMBA_CACHE_DIR /tmp/MPLCONFIGDIR && chmod 777 /home/speaker-diarization/data/ \
    && wget --content-disposition https://api.ngc.nvidia.com/v2/models/nvidia/nemo/titanet_large/versions/v0/zip -O titanet_large_v0.zip \
    && apt install zip -y \
    && mkdir -p NeMo_1.9.0rc0/titanet-l/492c0ab8416139171dc18c21879a9e45 && mkdir -p NeMo_1.9.0rc0/stt_en_conformer_ctc_large/010120d9959425c7862c9843960b3235 \
    && unzip titanet_large_v0.zip -d NeMo_1.9.0rc0/titanet-l/492c0ab8416139171dc18c21879a9e45 \
    && wget --content-disposition https://api.ngc.nvidia.com/v2/models/nvidia/nemo/stt_en_conformer_ctc_large/versions/1.6.0/zip -O stt_en_conformer_ctc_large_1.6.0.zip \
    && unzip stt_en_conformer_ctc_large_1.6.0.zip -d NeMo_1.9.0rc0/stt_en_conformer_ctc_large/010120d9959425c7862c9843960b3235 \
    && wget --content-disposition https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/offline_diarization_with_asr.yaml \
    && mv offline_diarization_with_asr /home/speaker-diarization/data/offline_diarization_with_asr.yaml \
    && wget --content-disposition https://kaldi-asr.org/models/5/4gram_big.arpa.gz \
    && gzip -d 4gram_big.arpa.gz \
    && mv 4gram_big.arpa /home/speaker-diarization/data \
    && apt-get install -y ffmpeg \ 
    && git clone https://github.com/NVIDIA/apex \
    && rm titanet_large_v0.zip stt_en_conformer_ctc_large_1.6.0.zip

# RUN wget --content-disposition https://api.ngc.nvidia.com/v2/models/nvidia/nemo/titanet_large/versions/v0/zip -O titanet_large_v0.zip
# RUN apt install zip -y
# RUN mkdir -p NeMo_1.9.0rc0/titanet-l/492c0ab8416139171dc18c21879a9e45 && mkdir -p NeMo_1.9.0rc0/stt_en_conformer_ctc_large/010120d9959425c7862c9843960b3235
# RUN unzip titanet_large_v0.zip -d NeMo_1.9.0rc0/titanet-l/492c0ab8416139171dc18c21879a9e45

# RUN wget --content-disposition https://api.ngc.nvidia.com/v2/models/nvidia/nemo/stt_en_conformer_ctc_large/versions/1.6.0/zip -O stt_en_conformer_ctc_large_1.6.0.zip
# RUN unzip stt_en_conformer_ctc_large_1.6.0.zip -d NeMo_1.9.0rc0/stt_en_conformer_ctc_large/010120d9959425c7862c9843960b3235

# COPY NeMo_1.9.0rc0 /root/.cache/torch/NeMo/NeMo_1.9.0rc0/
# RUN wget --content-disposition https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/speaker_tasks/diarization/conf/offline_diarization_with_asr.yaml
# COPY data/input_manifest.json /home/speaker-diarization/data/input_manifest.json

# RUN wget --content-disposition https://kaldi-asr.org/models/5/4gram_big.arpa.gz
# RUN gzip -d 4gram_big.arpa.gz
# RUN mv 4gram_big.arpa /home/speaker-diarization/data

# COPY data/4gram_big.arpa /home/speaker-diarization/data

#install ffmpeg to avoid warning
# RUN apt-get install -y ffmpeg
# RUN git clone https://github.com/NVIDIA/apex

#install apex(nvidia) to avoid warning
WORKDIR /home/speaker-diarization/apex
ENV TORCH_CUDA_ARCH_LIST='compute capability'

RUN python3.8 -m pip install -v --disable-pip-version-check --no-cache-dir ./

WORKDIR /home/speaker-diarization/

# prevent log from kaldi
#RUN git clone https://github.com/kaldi-asr/kaldi.git
#RUN mkdir tmp && mv kaldi tmp/kaldi
#ENV KALDI_ROOT=/home/speaker-diarization/tmp/kaldi
COPY double-confirm-data-audio/ground_truth /home/speaker-diarization/double-confirm-data-audio/ground_truth
COPY server_speaker_diarization.py /home/speaker-diarization/
# COPY server_speaker_diarization.py /home/speaker-diarization/
CMD python3.8 -u server_speaker_diarization.py