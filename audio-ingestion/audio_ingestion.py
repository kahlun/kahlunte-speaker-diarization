# Copyright (c) 2019 Intel Corporation.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""EII Message Bus publisher example
"""

import logging
import os

import eii.msgbus as mb
import base64
from scipy.io import wavfile 
import time

import hashlib

level = logging.DEBUG
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s] - %(message)s",
    level=level,
)
logging.root.setLevel(level)
log = logging.getLogger()
log.setLevel(level)

msgbus = None
publisher = None

topic = os.environ.get("ZMQ_TOPIC") or "audio_for_speaker_diarization"
interval = int(os.environ.get("PUBLISH_INTERVAL")) or 10
audio_file_path = os.environ.get("AUDIO_FILE_PATH") or 'original-vistry-ffmpeg-1-minute.wav'

class EII_MB:
    def __init__(self) -> None:
        self.configuration = {
            "type": os.environ.get("ZMQ_TYPE") or "zmq_tcp",
            "zmq_tcp_publish": {
                "host": os.environ.get("ZMQ_HOST_IP") or "127.0.0.1",
                "port": int(os.environ.get("ZMQ_HOST_PORT")) or 3000,
            },
        }

    def get_config(self):
        return self.configuration

log.debug("Initializing EII Message Bus Configuration")
mb_config = EII_MB().get_config()

log.debug(f'ZMQ Type = \'{mb_config["type"]}\'')
log.debug(f'ZMQ Host IP = {mb_config["zmq_tcp_publish"]["host"]}')
log.debug(f'ZMQ Host Port = {mb_config["zmq_tcp_publish"]["port"]}')
log.debug(f"Interval between each publish = {interval} seconds")

log.debug("Initializing message bus context")
msgbus = mb.MsgbusContext(mb_config)

log.debug(f"Initializing publisher for topic '{topic}'")
publisher = msgbus.new_publisher(topic)

log.info("Running...")
try:

        # while True:
    sampling_rate, data = wavfile.read('audio_files/' + audio_file_path)
    # sampling_rate, data = wavfile.read(audio_file_path)
    to_send_base64 =  base64.b64encode(data)
    
    hash = hashlib.sha1()
    hash.update(str(time.time()).encode('utf-8'))
    unique_key = hash.hexdigest()
    
    meta = {
        'sampling_rate' : 16000,
        'last' : False,
        'id' : unique_key,
    }
    total = 0
    log.info("Publishing...")
    MAX_MB = 1024 * 1024 * 61
    # MAX_MB = 66961920 #tested largest file after convert base64
    chunks_length = int(len(to_send_base64) / MAX_MB)
    
    # though size limit issue, because 50mb, 50,221,542 bytes file fail, but < 5mb file pass without sleep.
    # this is the solution with chunk size + sleep, if send multiple chunk without sleep will fail too.
    def send_with_chunks(to_send_base64, meta):
        if(chunks_length is not 0): #no need chunk

            chunks, chunk_size = len(to_send_base64), int(len(to_send_base64)/chunks_length)
            to_send_list = [to_send_base64[i:i+chunk_size] for i in range (0, chunks, chunk_size)]

            for x in to_send_list:
                print('pushed')
                total+= len(x)
                if(x != to_send_list[-1]):
                    print('one chunk')
                    publisher.publish((meta, x))
                else:
                    print('last piece')
                    meta['last'] = True
                    publisher.publish((meta, x))
                time.sleep(0.1) # very important to sleep after assume it is published.
        else:
            publisher.publish((meta, to_send_base64))
            time.sleep(0.1) # very important to sleep after assume it is published.

    meta['last'] = True
    publisher.publish((meta, to_send_base64))
    time.sleep(0.1) # very important to sleep after assume it is published.

    log.info("Published...")

except KeyboardInterrupt:
    log.debug("Quitting...")
finally:
    if publisher is not None:
        publisher.close()