import glob
import os

# library speaker diarization
import time
import importlib
import os
import time
import glob
import pprint
pp = pprint.PrettyPrinter(indent=4)
import re

#library from summarization
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

#library use for benchmark ASR
import jiwer
from jiwer import cer
import re

import sys

# server needed
import eii.msgbus as mb

import logging
import datetime

level = logging.DEBUG
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s] - %(message)s",
    level=level,
)
logging.root.setLevel(level)
log = logging.getLogger()
log.setLevel(level)

overwrite_speaker_diarization = False # if output -> model -> wav already exist continue overwrite_speaker_diarization
overwrite_summarization = False # if output -> model -> wav already exist continue summarization

# if(len(sys.argv) > 1):
#     arg_overwrite_sd = sys.argv[1]
#     arg_overwrite_summarization = sys.argv[2]
#     overwrite_speaker_diarization = False if arg_overwrite_sd == '0' else True
#     overwrite_summarization = False if arg_overwrite_summarization == '0' else True

ROOT = os.getcwd()
data_dir = os.path.join(ROOT,'data/output')

text_ref_youtube = open('double-confirm-data-audio/ground_truth' + '/youtube-subtitle-author' +'.txt', 'r').read() #ground truth youtube
text_ref_vistry = open('double-confirm-data-audio/ground_truth' + '/vistry-subtitle-self' +'.txt', 'r').read() #ground truth vistry
file_dir = 'data'
model_name = 'philschmid/bart-large-cnn-samsum' ## to be retrieve from os.environment

global model
global tokenizer
def store_model_and_tokenizer(model_name):
    path_model_summarization = 'model/summarization'
    os.makedirs(path_model_summarization, exist_ok=True)
    path_model_summarization += '/' + str(model_name)
    print(path_model_summarization)
    log.info(path_model_summarization)
    global model
    global tokenizer
    model = AutoModelForSeq2SeqLM.from_pretrained(path_model_summarization)
    tokenizer = AutoTokenizer.from_pretrained(path_model_summarization)
store_model_and_tokenizer(model_name) 
def main(text_lm):
    
    #change None to list to only do 1 time speaker diarization
    t_start = time.perf_counter()
    global data_dir
    os.makedirs(data_dir, exist_ok=True)
    summarized_text = ''
    
    def summarization_and_benchmark():
        if(os.path.exists(file_dir+'/dialogue.txt')):
            # text_lm = open('dialogue.txt', 'r').read()
            # summarize(text_lm , file_dir, asr_model_name + '-' + feature_model_name + '-summary.txt', 'philschmid/bart-large-cnn-samsum')
            summarized_text = summarize(text_lm , file_dir, 'dialogue.txt') # only interested in text
            return summarized_text
        else:
            print("unexpected behavior, file missing when summarization and benchmark ")

    summarized_text = summarization_and_benchmark()['summary']
    t_end = time.perf_counter()
    return {
        'summary' : summarized_text,
        'execution_time' : str(datetime.timedelta(seconds= t_end - t_start))
    }

# expected model and tokenizer from global variable.
# so can reduce time execution in loading it
def summarize(text, file_dir, file_name):
    save_model = False
    summary_path = file_dir + '/summary'
    summary_file_path = summary_path + '/' + file_name
    # if(not overwrite_summarization and os.path.exists(summary_file_path)): #skip this .wav file for summarization
    #     print(" skip task summarization : " + file_name + '\n')
    #     print(summary_file_path)
    #     return
    print('start summarization')
    os.makedirs(summary_path, exist_ok=True)
    t_start = time.perf_counter()
    regex = r'[[0-2][0-9]:[0-9][0-9].[0-9][0-9] - [0-2][0-9]:[0-9][0-9].[0-9][0-9]]'

    conversation = text
    # conversation = re.sub(r'[[0-2][0-9]:[0-9][0-9].[0-9][0-9] - [0-2][0-9]:[0-9][0-9].[0-9][0-9]]', '', conversation)
    conversation = re.sub(r'[[0-9][0-9]:[0-9][0-9].[0-9][0-9] - [0-2][0-9]:[0-9][0-9].[0-9][0-9]]', '', conversation) #remove string for audio timestamp
    
    conversation = conversation[:3000]
    # print(conversation, 'truncated text')

    inputs = tokenizer("summarize: " + conversation, return_tensors="pt", max_length=1024, truncation=False)
    result = model.generate(
        inputs["input_ids"], max_length=1024, min_length=40, length_penalty=2.0, num_beams=4, early_stopping=False
    )
    # print(tokenizer.decode(result[0]))
    
    with open(summary_file_path,'w') as fp:
        fp.write('Truncated Text : \n')
        fp.write(conversation)
        fp.write('\n')
        fp.write('Summary As : \n')
        fp.write(tokenizer.decode(result[0]))
        fp.write('\n')

    t_end = time.perf_counter()
    # print("summarize time consumed", t_end - t_start)
    # return [tokenizer.decode(result[0]), t_end]
    return {
        'summary' : tokenizer.decode(result[0]),
        'execution time (H:M:S) ' : t_end - t_start,
    }

#not using for container yet
def benchmark(file_dir, hypothesis, compare_file_name):
    
    benchmark_path = file_dir + '/benchmark'
    benchmark_file_path = benchmark_path + '/' + compare_file_name
    os.makedirs(benchmark_path, exist_ok=True)
    
    if('youtube' in compare_file_name):
        ground_truth = text_ref_youtube 
        ground_truth = ground_truth.replace("Vanessa:", "speaker_0:")
        ground_truth = ground_truth.replace("Charisse:", "speaker_1:")
        
    elif('vistry' in compare_file_name): 
        ground_truth = text_ref_vistry
        print('detect benchmark for vistry , no preprocess to ground truth.')
        
    hypothesis = re.sub(r'[[0-2][0-9]:[0-9][0-9].[0-9][0-9] - [0-2][0-9]:[0-9][0-9].[0-9][0-9]]', '', hypothesis)
    
    transformation = jiwer.Compose([
        jiwer.RemovePunctuation(),
        jiwer.Strip(),
        jiwer.ExpandCommonEnglishContractions(),
        jiwer.ToLowerCase(),
        jiwer.RemoveWhiteSpace(replace_by_space=True),
        jiwer.RemoveMultipleSpaces(),
        jiwer.ReduceToListOfListOfWords(word_delimiter=" "),
        # jiwer.ReduceToSingleSentence(),
    ]) 
    measures = jiwer.compute_measures(ground_truth, hypothesis, truth_transform = transformation, hypothesis_transform = transformation)
    wer = measures['wer']
    mer = measures['mer']
    wil = measures['wil']
    cer_rate = cer(ground_truth, hypothesis)
    print('benchmark_file_path', benchmark_file_path)
    with open(benchmark_file_path,'w') as fp:
        fp.write(compare_file_name + ' compare_file_name')
        fp.write('\n')
        fp.write('result')
        fp.write('\n')
        fp.write(str(wer * 100) + ' wer (word error rate)')
        fp.write('\n')
        fp.write(str(mer * 100) + ' mer (match error rate)')
        fp.write('\n')
        fp.write(str(wil * 100) + ' wil (word information lost)')
        fp.write('\n')
        fp.write(str(cer_rate * 100) + ' cer (character error rate)')
        fp.write('\n')
        fp.write('end')
        fp.write('\n')

zmq_topic = (
    os.environ.get("ZMQ_TOPIC_TS")
    if os.environ.get("ZMQ_TOPIC_TS") != None
    else "text_summarization"
)

mb_config = {
    "type": os.environ.get("ZMQ_TYPE_TS")
    if os.environ.get("ZMQ_TYPE_TS") != None
    else "zmq_tcp",
    zmq_topic: {
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
try:

    log.info('Running...')
    log.debug("Collector Thread") 
    log.debug("Initializing message bus context for text summarization")
    msgbus = mb.MsgbusContext(mb_config)

    log.debug(f"Initializing subscriber for topic '{zmq_topic}'")
    subscriber = msgbus.new_subscriber(zmq_topic)
    while True:

        log.info('Running... receiver')
        msg = subscriber.recv()
        
        response_meta_data = msg.get_meta_data()
        text = response_meta_data['text'][0]
        temp_txt_file = file_dir + '/dialogue.txt'
        with open(temp_txt_file,'w') as fp:
            fp.write(text)

        summarizer_response = main(text)
        
        # should be no need remove, because now the file is not unique.
        # try:
        #     os.remove(temp_txt_file)
        # except Exception as e:
        #     print(e)
        #     pass
        log.info("summarized text")
        log.info(summarizer_response['summary'])
        
        log.info("execution time (H:M:S)")
        log.info(summarizer_response['execution_time'])
        
        log.info('finish one summarization')
except KeyboardInterrupt:
    print('[INFO] Quitting...')
finally:
    if subscriber is not None:
        subscriber.close()
