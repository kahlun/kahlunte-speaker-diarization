FROM ubuntu:20.04

LABEL description="TTS Image"
LABEL vendor="Intel Corporation"

USER root

RUN mkdir -p /home/tts/env

COPY tts_cache.py /home/tts/
COPY hashing.py /home/tts/
COPY data_compress_decompress.py /home/tts/
COPY logger.py /home/tts/
COPY text_to_speech_demo.py /home/tts/
COPY tts_server.py /home/tts/
COPY models.lst /home/tts/
COPY requirements.txt /home/tts/
COPY utils /home/tts/utils
COPY models /home/tts/models
COPY protos /home/tts/protos
COPY openvino_installation_files /home/tts/openvino_installation_files
COPY model_conversion /home/tts/model_conversion

WORKDIR /home/tts/

RUN apt update \
    && apt install -y python3.9  \
    && apt install python3.9-dev -y \
    && apt install -y python3.9-venv \
    && apt install wget -y \
    && apt install gcc -y \ 
    && apt install git -y \
    && apt install libsndfile1-dev -y \
    && python3.9 -m venv openvino_3.9 \
    && . openvino_3.9/bin/activate \
    && apt install libpython3.9 \
    && python3 -m pip install --upgrade pip \ 
    && python3 -m pip install openvino_installation_files/openvino-2022.2.0.dev20220329-7201-cp39-cp39-manylinux_2_27_x86_64.whl \
    && python3 -m pip install openvino_installation_files/openvino_dev-2022.2.0.dev20220329-7201-py3-none-any.whl \
    && python3 -m pip install matplotlib Cpython Cython unidecode librosa==0.8.1 torch==1.9.1 \
    && python3 -m pip install inflect>=5.3.0 \
    && omz_downloader --name text-to-speech-en-multi-????-* --precisions FP32 \
    && cd model_conversion  \
    && chmod +x model_conversion.sh \
    && ./model_conversion.sh \
    && cd .. \
    && rm -r openvino_3.9 \
 #   && python -m pip uninstall  matplotlib -y Cpython -y Cython -y unidecode -y librosa==0.8.1 -y   torch==1.9.1 -y \
    && python3.9 -m venv openvino_3.9 \
    && . openvino_3.9/bin/activate \
    && python3 -m pip install --upgrade pip \ 
    && python3 -m pip install openvino_installation_files/openvino-2022.2.0.dev20220329-7201-cp39-cp39-manylinux_2_27_x86_64.whl \
    && python3 -m pip install -r requirements.txt \
    && python3 -m grpc_tools.protoc -I /home/tts/protos --python_out=/home/tts/ --grpc_python_out=/home/tts/ tts.proto \
    && rm -r openvino_installation_files \
    && rm model_openvino/*.mapping \
    && apt remove python3.9-dev -y \
    && apt remove wget -y \
    && apt remove gcc -y \ 
    && apt remove git -y \
    && apt remove libsndfile1-dev -y \
    && apt autoremove -y \
    && python -m pip uninstall pip setuptools -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/archives \
    && rm -rf /root/.cache/*

HEALTHCHECK NONE

CMD . openvino_3.9/bin/activate \ 
    &&  python3 /home/tts/tts_server.py

