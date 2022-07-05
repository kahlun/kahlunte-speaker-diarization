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
"""EII Message Bus echo service Python example.
"""
profile = lambda f: f
import json
import argparse

from pandas import concat
import eii.msgbus as mb
import time
import glob
import os

# library speaker diarization
import time
import importlib
import nemo.collections.asr.parts.utils.diarization_utils as diarization_utils
from omegaconf import OmegaConf
import json
import shutil
from nemo.collections.asr.parts.utils.decoder_timestamps_utils import ASR_TIMESTAMPS
from nemo.collections.asr.parts.utils.diarization_utils import ASR_DIAR_OFFLINE
from nemo.collections.asr.parts.utils.speaker_utils import rttm_to_labels
import gzip
import importlib
import nemo.collections.asr.parts.utils.decoder_timestamps_utils as decoder_timestamps_utils
import os
import wget
import time
import glob
import pprint
pp = pprint.PrettyPrinter(indent=4)
import re
import datetime

#library from summarization
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

#library use for benchmark ASR
from jiwer import cer
import re

# server needed
import numpy as np
import base64
from  scipy.io import wavfile 
import logging

# logging.disable(logging.CRITICAL)
# logging.getLogger('nemo_logger').setLevel(logging.ERROR)

level = logging.DEBUG
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s] - %(message)s",
    level=level,
)
logging.root.setLevel(level)
log = logging.getLogger()
log.setLevel(level)
# logging.getLogger('nemo_logger').propagate = False



# logging.disable(logging.CRITICAL)

# Argument parsing
# ap = argparse.ArgumentParser()
# ap.add_argument('-s', '--service-name', dest='service_name',
#                 default='speaker_diarization', help='Service name')
# args = ap.parse_args()

msgbus = None
service = None

# mb_config = {
#     "type": "zmq_tcp",
#     "speaker_diarization": {
#         "host": "127.0.0.1",
#         "port": 8675
#     }
# }

server_service_name = (
    os.environ.get("ZMQ_TOPIC_SD")
    if os.environ.get("ZMQ_TOPIC_SD") != None
    else "audio_for_speaker_diarization"
)

mb_config = {
    "type": os.environ.get("ZMQ_TYPE_SD")
    if os.environ.get("ZMQ_TYPE_SD") != None
    else "zmq_tcp",
    server_service_name: {
        "host": os.environ.get("ZMQ_HOST_IP_SD")
        if os.environ.get("ZMQ_HOST_IP_SD") != None
        else "127.0.0.1",
        "port": int(
            os.environ.get("ZMQ_HOST_PORT_SD")
            if os.environ.get("ZMQ_HOST_PORT_SD") != None
            else 3000
        ),
    },
}
# source code of speaker_diarization

model_path = 'model/Nemo/NeMo_1.9.0rc0'

overwrite_speaker_diarization = True # if output -> model -> wav already exist continue overwrite_speaker_diarization
overwrite_summarization = True # if output -> model -> wav already exist continue summarization

# asr_model_name_list = ['QuartzNet15x5Base-En', 'stt_en_conformer_ctc_large'] # change index to pick model
# model_variant = 'stt_en_conformer_ctc_xlarge'
model_variant = 'stt_en_conformer_ctc_large'
asr_model_name_list = [model_path + '/'+model_variant+'/010120d9959425c7862c9843960b3235/'+model_variant+'.nemo'] # change index to pick model
# speaker_embedding_feature_model_name_list = [model_path + '/titanet_large']
speaker_embedding_feature_model_name_list = [model_path + '/titanet-l/492c0ab8416139171dc18c21879a9e45/titanet-l.nemo']

defined_model_asr_feature = None # ['stt_en_conformer_ctc_large', 'titanet_large'] for single speaker diarization
ROOT = os.getcwd()
shared_files_dir = os.path.join(ROOT,'data')
audio_file_path = shared_files_dir + '/audio_files'

config_yaml = "offline_diarization_with_asr.yaml" #assumed exist in ./data
data_dir = os.path.join(ROOT,'data/output')
ARPA_URL = 'https://kaldi-asr.org/models/5/4gram_big.arpa.gz'

text_ref_youtube = open('double-confirm-data-audio/ground_truth' + '/youtube-subtitle-author' +'.txt', 'r').read() #ground truth youtube
text_ref_vistry = open('double-confirm-data-audio/ground_truth' + '/vistry-subtitle-self' +'.txt', 'r').read() #ground truth vistry
@profile
def main(file_name):
    # audio_file_list = glob.glob(f"{audio_file_path}/*.wav")
    audio_file_list = glob.glob(f"{audio_file_path}/*.wav") # remove support for multiple wav file
    text_lm_list = []
    response = {
        'dialogues' : [],
        'execution_time': -1,
    }
    #change None to list to only do 1 time speaker diarization
    t_start = time.perf_counter()
    global data_dir
    os.makedirs(data_dir, exist_ok=True)

    def summarization_and_benchmark():
        print(file_dir, 'file_dir', 'summarization_and_benchmark')
        if(os.path.exists(file_dir + '/pred_rttms/' + audio_file_name_no_extension +'.txt')):
            text_lm = open(file_dir + '/pred_rttms/' + audio_file_name_no_extension +'.txt', 'r').read()
            # for debug 
            # text_no_lm = open(file_dir + '/pred_rttms/' + "-no-language-model"+audio_file_name_no_extension +'.txt', 'r').read()
            # create_diaogue_without_timestamp(file_dir + '/pred_rttms/' + "no-language-model-dialogue"+audio_file_name_no_extension +'.txt', text_no_lm, asr_model_name + '-' + feature_model_name + '-' + audio_file_name_no_extension + '-no-language-model-dialogue.txt') # for 
            # create_diaogue_without_timestamp(file_dir + '/pred_rttms/' + "language-model-dialogue"+audio_file_name_no_extension +'.txt', text_lm, asr_model_name + '-' + feature_model_name + '-' + audio_file_name_no_extension + '-language-model-dialogue.txt') # for 
            return text_lm
        else:
            print("unexpected behavior, file missing when summarization and benchmark ", file_dir + '/pred_rttms/' + audio_file_name_no_extension +'.txt')

    for asr_model_name in asr_model_name_list:
        for feature_model_name in speaker_embedding_feature_model_name_list:
            data_dir = os.path.join(ROOT,'data/output/'+ asr_model_name + '-' + feature_model_name)
            os.makedirs(data_dir, exist_ok=True)
            # for audio_file_absolute_path in audio_file_list: # layer for all .wav files
            #     file_name = audio_file_absolute_path
            #     audio_file_absolute_path = file_name
            #     audio_file_name_no_extension = os.path.splitext(os.path.basename(audio_file_absolute_path))[0] #variable, new folder name
            #     file_dir = data_dir + "/" + audio_file_name_no_extension
            #     speaker_diarization(file_name, data_dir, asr_model_name, feature_model_name)
            #     text_lm_list.append(summarization_and_benchmark())
            #     logging.info('output : ')
            
            # remove support for list of wav files.
            
            audio_file_absolute_path = file_name
            audio_file_name_no_extension = os.path.splitext(os.path.basename(audio_file_absolute_path))[0] #variable, new folder name
            file_dir = data_dir + "/" + audio_file_name_no_extension
            speaker_diarization(file_name, data_dir, asr_model_name, feature_model_name)
            text_lm_list.append(summarization_and_benchmark())
            logging.info('output : ')
                
                
                
    t_end = time.perf_counter()
    response['execution_time'] = t_end
    logging.info("Speaker diarization Done. ")
    logging.info("Result . . . .")
    if(text_lm_list[0]):
        logging.info(text_lm_list[0])
    else:
        logging.info('no audio file processed')
    # logging.info("time consumed (whole loop)", t_end - t_start)
    logging.info("time consumed (whole loop) H:M:S " + str(datetime.timedelta(seconds= t_end - t_start)))
    logging.info("Result end . . . .")
    
    for single_dialogue in text_lm_list:
        response['dialogues'].append(single_dialogue)
    
    return response
@profile
def speaker_diarization(file_name, data_dir, asr_model_name, feature_model_name):
    
    def get_config():
        CONFIG = os.path.join(shared_files_dir, config_yaml)
        cfg = OmegaConf.load(CONFIG)
        cfg.diarizer.manifest_filepath = os.path.join(shared_files_dir,'input_manifest.json')
        """Let's set the parameters required for diarization. In this tutorial, we obtain voice activity labels from ASR, which is set through parameter `cfg.diarizer.asr.parameters.asr_based_vad`."""
        cfg.diarizer.out_dir = file_dir #Directory to store intermediate files and prediction outputs
        cfg.diarizer.speaker_embeddings.parameters.window_length_in_sec = 1.5
        cfg.diarizer.speaker_embeddings.parameters.shift_length_in_sec = 0.75
        cfg.diarizer.clustering.parameters.oracle_num_speakers=True
        # Using VAD generated from ASR timestamps

        cfg.diarizer.oracle_vad = False # ----> Not using oracle VAD 
        cfg.diarizer.asr.parameters.asr_based_vad = True
        cfg.diarizer.asr.parameters.threshold=100 # ASR based VAD threshold: If 100, all silences under 1 sec are ignored.
        cfg.diarizer.asr.parameters.decoder_delay_in_sec=0.2 # Decoder delay is compensated for 0.2 sec
        return cfg
    
    def create_input_manifest():
        meta = {
            'audio_filepath': file_name, 
            'offset': 0, 
            'duration':None, 
            'label': 'infer', 
            'text': '-', 
            # 'oracle_num_speakers' : False,
            'num_speakers': 2, 
            'rttm_filepath': None, 
            'uem_filepath' : None
        }
        with open(os.path.join(shared_files_dir,'input_manifest.json'),'w') as fp:
            json.dump(meta,fp)
            fp.write('\n')
    
    def read_file(path_to_file):
        with open(path_to_file) as f:
            contents = f.read().splitlines()
        return contents
    
    logging.info('start speaker diarization')
    t_start = time.perf_counter()
    audio_file_absolute_path = file_name
    audio_file_name_no_extension = os.path.splitext(os.path.basename(audio_file_absolute_path))[0] #variable, new folder name
    file_dir = data_dir + "/" + audio_file_name_no_extension
    if(os.path.exists(file_dir+ '/pred_rttms/'+audio_file_name_no_extension+'.txt')  and not overwrite_speaker_diarization): #skip this .wav file for speaker diarization
        print("skipped 1 file", os.path.basename(audio_file_absolute_path))
        print("task : " + asr_model_name + '-' + feature_model_name)
        return
    os.makedirs(file_dir, exist_ok=True)
    path_pred_rttms = file_dir +  "/"+ "pred_rttms"
    os.makedirs(path_pred_rttms, exist_ok=True)
    
    ##start inference / process speaker diarization
    create_input_manifest()    
    cfg = get_config()
    cfg.diarizer.manifest_filepath = os.path.join(shared_files_dir,'input_manifest.json')
    # cfg.diarizer.asr.model_path = 'stt_en_conformer_ctc_large'
    cfg.diarizer.asr.model_path = asr_model_name
    # asr_model_name
    # feature_model_name = 'ecapa_tdnn'
    cfg.diarizer.speaker_embeddings.model_path = feature_model_name
    cfg.diarizer.out_dir = file_dir #Directory to store intermediate files and prediction outputs
    arpa_model_path = os.path.join(shared_files_dir, '4gram_big.arpa')
    
    cfg.diarizer.asr.ctc_decoder_parameters.pretrained_language_model = arpa_model_path
                                         
    importlib.reload(decoder_timestamps_utils) # This module should be reloaded after you install pyctcdecode.

    asr_ts_decoder = ASR_TIMESTAMPS(**cfg.diarizer)
    logging.info('loaded ASR timestamp configuration')
    
    logging.info('setting up ASR time stamp model')
    asr_model = asr_ts_decoder.set_asr_model()
    logging.info('loaded ASR time stamp model')
    
    logging.info('running ASR time stamp model')
    word_hyp, word_ts_hyp = asr_ts_decoder.run_ASR(asr_model)
    logging.info('prepared hypothesis of word and its timestamp')

    # print("Decoded word output dictionary: \n", word_hyp[audio_file_name_no_extension])
    # print("Word-level timestamps dictionary: \n", word_ts_hyp[audio_file_name_no_extension])

    cfg.diarizer.asr.realigning_lm_parameters.arpa_language_model = arpa_model_path
    cfg.diarizer.asr.realigning_lm_parameters.logprob_diff_threshold = 1.2

    importlib.reload(diarization_utils) # This module should be reloaded after you install arpa.
    
    logging.info('loading speaker diarization & ASR configuration')
    asr_diar_offline = ASR_DIAR_OFFLINE(**cfg.diarizer)
    logging.info('loaded speaker diarization & ASR configuration')
    
    asr_diar_offline.word_ts_anchor_offset = asr_ts_decoder.word_ts_anchor_offset
    
    logging.info('running speaker diarization with word timestamp hypothesis')
    diar_hyp, diar_score = asr_diar_offline.run_diarization(cfg, word_ts_hyp) 
    logging.info('completed speaker diarization')
    
    logging.info('running aligning speaker diarization, word hypothesis, word time stamp hypothesis')
    asr_diar_offline.get_transcript_with_speaker_labels(diar_hyp, word_hyp, word_ts_hyp)
    logging.info('finish aligning speaker diarization, word hypothesis, word time stamp hypothesis')

    logging.info('recording the result (dialogue) to file')
    transcription_path_to_file = f"{path_pred_rttms}/"+audio_file_name_no_extension+".txt" 
    logging.info('recorded result')
    
    transcript = read_file(transcription_path_to_file)
    # pp.pprint(transcript)

    t_end = time.perf_counter()
    logging.info('completed speaker diarization with language model')
    # print("time consumed", t_end - t_start)
    
@profile
def create_diaogue_without_timestamp(file_path, text, file_name):
    print('write dialogue no time stamp', file_name )
    text = re.sub(r'[[0-2][0-9]:[0-9][0-9].[0-9][0-9] - [0-2][0-9]:[0-9][0-9].[0-9][0-9]]', '', text)

    with open(file_path,'w') as fp:
        fp.write(text + file_name)

@profile
# EII publisher to Text summarization
def publish_to_text_summarization(text):
    
    zmq_topic = (
        os.environ.get("ZMQ_TOPIC_TS")
        if os.environ.get("ZMQ_TOPIC_TS") != None
        else "text_summarization"
    )

    mb_config = {
        "type": os.environ.get("ZMQ_TYPE_TS")
        if os.environ.get("ZMQ_TYPE_TS") != None
        else "zmq_tcp",
        'zmq_tcp_publish': {
            "host": os.environ.get("ZMQ_HOST_IP_TS")
            if os.environ.get("ZMQ_HOST_IP_TS") != None
            else "127.0.0.1",
            "port": int(
                os.environ.get("ZMQ_HOST_PORT_TS")
                if os.environ.get("ZMQ_HOST_PORT_TS") != None
                else 3001
            ),
        },
    }
    
    log.info("Initializing message bus context for text summarization")
    msgbus = mb.MsgbusContext(mb_config)

    log.info(f"Initializing publisher for topic '{zmq_topic}'")
    publisher = msgbus.new_publisher(zmq_topic)

    # while True:
    meta = {
        'text' : text,
    }
    log.info("Publishing...")
    publisher.publish(meta)
    log.info("Published...")
    publisher.close()

try:
    log.info("Running...")
    msgbus = None
    subscriber = None

    """This is the producer thread.
    It will produce text data for the intel's speaker_diarization engine."""
    zmq_topic = (
        os.environ.get("ZMQ_TOPIC_SD")
        if os.environ.get("ZMQ_TOPIC_SD") != None
        else "audio_for_speaker_diarization"
    )

    mb_config = {
        "type": os.environ.get("ZMQ_TYPE_SD")
        if os.environ.get("ZMQ_TYPE_SD") != None
        else "zmq_tcp",
        zmq_topic: {
            "host": os.environ.get("ZMQ_HOST_IP_SD")
            if os.environ.get("ZMQ_HOST_IP_SD") != None
            else "127.0.0.1",
            "port": int(
                os.environ.get("ZMQ_HOST_PORT_SD")
                if os.environ.get("ZMQ_HOST_PORT_SD") != None
                else 3000
            ),
        },
        'ZMQ_MAXMSGSIZE' : -1,
    }
    
    log.info("Collector Thread")
    log.info("Initializing message bus context")
    msgbus = mb.MsgbusContext(mb_config)

    log.info(f"Initializing subscriber for topic '{zmq_topic}'")
    subscriber = msgbus.new_subscriber(zmq_topic)
    a = 0
    
    dict_file_chunked = {}
    id = None
    while True:
    # while (a<1):
        # while True:
        log.info(f"subscribing for topic '{zmq_topic}'")
        log.info(f"subscribing for topic hello, modified'")
        msg = subscriber.recv()
        log.info("received")
        
        response_blob = msg.get_blob()
        received_meta_data = msg.get_meta_data()
        
        # rmb settle id1 with meta_data
        if(received_meta_data['id'] in dict_file_chunked):
            continue
        elif('id' in received_meta_data):
            dict_file_chunked[received_meta_data['id']] = {
                'data' : b'',
                'last': False,
            }
        id = received_meta_data['id']
        dict_file_chunked[id]['data'] += response_blob
        
        if(received_meta_data['last']):
            log.info('detected final pieces, combining')
            response_blob = dict_file_chunked[id]['data']
            r = base64.decodebytes(response_blob)
            dict_file_chunked.pop(id, None)
            # response_as_np_array = np.frombuffer(r, dtype=np.int32)
            received_file_dtype = received_meta_data['dtype']
            response_as_np_array = np.frombuffer(r, dtype=np.dtype(getattr(np, received_file_dtype)))
            # response_as_np_array = np.frombuffer(response_blob, dtype=np.int32)
            if 'sampling_rate' in received_meta_data:
                sampling_rate = received_meta_data['sampling_rate']
            else: 
                sampling_rate = received_meta_data
            
            temp_wav_file = 'data/audio_files/' + id + '-server-wav-scipy.wav'
            wavfile.write(temp_wav_file, received_meta_data['sampling_rate'], response_as_np_array)
            response = main(temp_wav_file)
            publish_to_text_summarization(response['dialogues'])
            try:
                os.remove(temp_wav_file)
            except OSError:
                pass
            log.info("done one speaker diarization")
        else:
            log.info('this round no complete file, not doing speaker diarizarion')
        
        a+=1
        
except KeyboardInterrupt:
    print('[INFO] Quitting...')
finally:
    if service is not None:
        service.close()
