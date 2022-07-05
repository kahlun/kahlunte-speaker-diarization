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



WORKDIR /home/audio_ingestion

RUN pip3 install -r /home/audio_ingestion/requirements.txt \
    && python3 -m grpc_tools.protoc -I ./protos/ --python_out=./src/ --grpc_python_out=./src/ audio_ingestion.proto

COPY audio-ingestion-grpc-server/protos /home/audio_ingestion/protos
COPY audio-ingestion-grpc-server/src /home/audio_ingestion/src

COPY audio-ingestion-grpc-server/requirements.txt /home/audio_ingestion/

RUN python3.8 -m pip install -r requirements.txt
CMD python3 src/server.py
