#!/usr/bin/env python3

"""
 Copyright (c) 2020-2022 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import sys
import logging as log
from time import perf_counter
from argparse import ArgumentParser, SUPPRESS

from tqdm import tqdm
import numpy as np
import wave
from openvino.runtime import Core, get_version

from models.forward_tacotron_ie import ForwardTacotronIE
from models.mel2wave_ie import WaveRNNIE, MelGANIE
from models.glow_tts_ie import GlowTTSIE
from models.hifi2wav import MelGANIE as hifi

# from utils.gui import init_parameters_interactive
import logger as config

log = config.get_logger()


def save_wav(x, path):
    sr = 22050

    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(x.tobytes())


def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group("Options")
    args.add_argument(
        "-h",
        "--help",
        action="help",
        default=SUPPRESS,
        help="Show this help message and exit.",
    )
    args.add_argument(
        "-m_duration",
        "--model_duration",
        help="Required. Path to ForwardTacotron`s duration prediction part (*.xml format).",
        required=True,
        type=str,
    )
    args.add_argument(
        "-m_forward",
        "--model_forward",
        help="Required. Path to ForwardTacotron`s mel-spectrogram regression part (*.xml format).",
        required=True,
        type=str,
    )
    args.add_argument(
        "-i",
        "--input",
        help="Required. Text or path to the input file.",
        required=True,
        type=str,
        nargs="*",
    )
    args.add_argument(
        "-o",
        "--out",
        help="Optional. Path to an output .wav file",
        default="out.wav",
        type=str,
    )

    args.add_argument(
        "-d",
        "--device",
        help="Optional. Specify the target device to infer on; CPU, GPU, HDDL, MYRIAD or HETERO is "
        "acceptable. The demo will look for a suitable plugin for device specified. "
        "Default value is CPU",
        default="CPU",
        type=str,
    )

    args.add_argument(
        "-m_upsample",
        "--model_upsample",
        help="Path to WaveRNN`s part for mel-spectrogram upsampling "
        "by time axis (*.xml format).",
        default=None,
        required=False,
        type=str,
    )
    args.add_argument(
        "-m_rnn",
        "--model_rnn",
        help="Path to WaveRNN`s part for waveform autoregression (*.xml format).",
        default=None,
        required=False,
        type=str,
    )
    args.add_argument(
        "--upsampler_width",
        default=-1,
        help="Width for reshaping of the model_upsample in WaveRNN vocoder. "
        "If -1 then no reshape. Do not use with FP16 model.",
        required=False,
        type=int,
    )

    args.add_argument(
        "-m_melgan",
        "--model_melgan",
        help="Path to model of the MelGAN (*.xml format).",
        default=None,
        required=False,
        type=str,
    )

    args.add_argument(
        "-s_id",
        "--speaker_id",
        help="Ordinal number of the speaker in embeddings array for multi-speaker model. "
        "If -1 then activates the multi-speaker TTS model parameters selection window.",
        default=19,
        required=False,
        type=int,
    )

    args.add_argument(
        "-a",
        "--alpha",
        help="Coefficient for controlling of the speech time (inversely proportional to speed).",
        default=1.0,
        required=False,
        type=float,
    )

    return parser


def is_correct_args(args):
    if not (
        (
            args.model_melgan is None
            and args.model_rnn is not None
            and args.model_upsample is not None
        )
        or (
            args.model_melgan is not None
            and args.model_rnn is None
            and args.model_upsample is None
        )
    ):
        log.error(
            "Can not use m_rnn and m_upsample with m_melgan. Define m_melgan or [m_rnn, m_upsample]"
        )
        return False
    if args.alpha < 0.5 or args.alpha > 2.0:
        log.error("Can not use time coefficient less than 0.5 or greater than 2.0")
        return False
    if args.speaker_id < -1 or args.speaker_id > 39:
        log.error(
            "Mistake in the range of args.speaker_id. Speaker_id should be -1 (GUI regime) or in range [0,39]"
        )
        return False

    return True


def parse_input(input):
    if not input:
        return
    sentences = []
    for text in input:
        if text.endswith(".txt"):
            try:
                with open(text, "r", encoding="utf8") as f:
                    sentences += f.readlines()
                continue
            except OSError:
                pass
        sentences.append(text)
    return sentences


def main():
    args = build_argparser().parse_args()

    if not is_correct_args(args):
        return 1

    log.info("OpenVINO Runtime")
    log.info("\tbuild: {}".format(get_version()))
    core = Core()

    if args.model_melgan is not None:
        vocoder = MelGANIE(args.model_melgan, core, device=args.device)
    else:
        vocoder = WaveRNNIE(
            args.model_upsample,
            args.model_rnn,
            core,
            device=args.device,
            upsampler_width=args.upsampler_width,
        )

    forward_tacotron = ForwardTacotronIE(
        args.model_duration, args.model_forward, core, args.device, verbose=False
    )

    audio_res = np.array([], dtype=np.int16)

    speaker_emb = None
    if forward_tacotron.is_multi_speaker:
        if args.speaker_id == -1:
            interactive_parameter = init_parameters_interactive(args)
            args.alpha = 1.0 / interactive_parameter["speed"]
            speaker_emb = forward_tacotron.get_pca_speaker_embedding(
                interactive_parameter["gender"], interactive_parameter["style"]
            )
        else:
            speaker_emb = forward_tacotron.get_speaker_embeddings()[args.speaker_id, :]

    len_th = 512

    input_data = parse_input(args.input)

    time_forward = 0
    time_wavernn = 0

    time_s_all = perf_counter()
    count = 0
    for line in input_data:
        count += 1
        line = line.rstrip()
        log.info("Process line {0} with length {1}.".format(count, len(line)))

        if len(line) > len_th:
            texts = []
            prev_begin = 0
            delimiters = ".!?;:"
            for i, c in enumerate(line):
                if (c in delimiters and i - prev_begin > len_th) or i == len(line) - 1:
                    texts.append(line[prev_begin : i + 1])
                    prev_begin = i + 1
        else:
            texts = [line]

        for text in tqdm(texts):
            time_s = perf_counter()
            mel = forward_tacotron.forward(
                text, alpha=args.alpha, speaker_emb=speaker_emb
            )
            time_forward += perf_counter() - time_s

            time_s = perf_counter()
            audio = vocoder.forward(mel)
            time_wavernn += perf_counter() - time_s

            audio_res = np.append(audio_res, audio)

    total_latency = (perf_counter() - time_s_all) * 1e3
    log.info("Metrics report:")
    log.info("\tLatency: {:.1f} ms".format(total_latency))
    log.debug("\tVocoder time: {:.1f} ms".format(time_wavernn * 1e3))
    log.debug("\tForwardTacotronTime: {:.1f} ms".format(time_forward * 1e3))

    save_wav(audio_res, args.out)


# forward tacotron
def tts_main_ft_melgan(
    speaker_id,
    text_data,
    vocoder,
    forward_tacotron,
    alpha=1.0,
    gender="Male",
    style=1.0,
):
    input_data = [text_data]
    # time_s_all = time.perf_counter()

    audio_res = np.array([], dtype=np.int16)

    speaker_emb = None
    if forward_tacotron.is_multi_speaker:
        if speaker_id == -1:
            log.debug("Speaker Id not between 1 to 39")
            speaker_emb = forward_tacotron.get_pca_speaker_embedding(gender, style)
        else:
            log.debug("Setting Speaker Id")
            speaker_emb = [forward_tacotron.get_speaker_embeddings()[speaker_id, :]]

    # len_th = 512
    len_th = 80

    # texts = [input]

    # for text in tqdm(texts):
    #     mel = forward_tacotron.forward(text, alpha=alpha, speaker_emb=speaker_emb)
    #     audio = vocoder.forward(mel)
    #     time_e = time.perf_counter()
    #     audio_res = np.append(audio_res, audio)

    # time_e_all = time.perf_counter()
    # return(audio_res,time_e_all - time_s_all)
    time_forward = 0
    time_wavernn = 0

    time_s_all = perf_counter()

    count = 0
    for line in input_data:
        count += 1
        line = line.rstrip()
        log.info("Process line {0} with length {1}.".format(count, len(line)))

        if len(line) > len_th:
            texts = []
            prev_begin = 0
            delimiters = ".!?;:,"
            for i, c in enumerate(line):
                if (c in delimiters and i - prev_begin > len_th) or i == len(line) - 1:
                    texts.append(line[prev_begin : i + 1])
                    prev_begin = i + 1
        else:
            texts = [line]

        for text in tqdm(texts):
            time_s = perf_counter()
            mel = forward_tacotron.forward(text, alpha=alpha, speaker_emb=speaker_emb)
            time_forward += perf_counter() - time_s

            time_s = perf_counter()
            audio = vocoder.forward(mel)
            time_wavernn += perf_counter() - time_s

            audio_res = np.append(audio_res, audio)

    total_latency = (perf_counter() - time_s_all) * 1e3
    log.info("Metrics report:")
    log.info("\tLatency: {:.1f} ms".format(total_latency))
    log.debug("\tVocoder time: {:.1f} ms".format(time_wavernn * 1e3))
    log.debug("\tForwardTacotronTime: {:.1f} ms".format(time_forward * 1e3))

    log.debug("Returning Audio Output and Inference time")
    return (audio_res, total_latency)


def load_tts_ft_melgan():
    try:
        log.debug("Loading TTS")
        model_melgan = "./intel/text-to-speech-en-multi-0001/text-to-speech-en-multi-0001-generation/FP32/text-to-speech-en-multi-0001-generation.xml"
        model_duration = "./intel/text-to-speech-en-multi-0001/text-to-speech-en-multi-0001-duration-prediction/FP32/text-to-speech-en-multi-0001-duration-prediction.xml"
        model_forward = "./intel/text-to-speech-en-multi-0001/text-to-speech-en-multi-0001-regression/FP32/text-to-speech-en-multi-0001-regression.xml"
        # This is currently supported only for CPU
        target_device = "CPU"
        # ie = IECore()
        core = Core()
        try:
            log.debug("Load the MelGAN Model")
            vocoder = MelGANIE(model_melgan, core, device=target_device)
        except Exception as msg:
            log.error("Received Exception: {}".format(msg))
        try:
            log.debug("Load the Forward Tacotron Model")
            forward_tacotron = ForwardTacotronIE(
                model_duration, model_forward, core, target_device, verbose=False
            )
        except Exception as msg:
            log.error("Received Exception: {}".format(msg))
        return (vocoder, forward_tacotron)
    except Exception as msg:
        log.error("Received Excepton : {}".format(msg))


### Glow - TTS


def load_vocoder(m_vocoder, ie, device):
    if m_vocoder is not None:
        vocoder = hifi(m_vocoder, ie, device=device)
    return vocoder


def load_acoustic_model(m_acoustic, ie, device):
    if m_acoustic is not None:
        acoustic_model = GlowTTSIE(m_acoustic, ie, device, verbose=False)
        return acoustic_model, None


def load_tts_glow_hifigan():
    m_acoustic = "./model_openvino/glow-tts-blank.xml"
    m_vocoder = "./model_openvino/LJ_FT_T2_V1.xml"
    device = "CPU"
    ie = Core()
    vocoder = load_vocoder(m_vocoder, ie, device)
    acoustic_model, speaker_emb = load_acoustic_model(m_acoustic, ie, device)
    return vocoder, acoustic_model


def tts_main_glow_hifigan(speaker_id, text_data, vocoder, acoustic_model):
    speaker_emb = None
    audio_res = np.array([], dtype=np.int16)

    len_th = 512

    input_data = [text_data]

    time_acoustic_model = 0
    time_vocoder = 0

    time_s_all = perf_counter()
    count = 0
    for line in input_data:
        count += 1
        line = line.rstrip()
        log.info("Process line {0} with length {1}.".format(count, len(line)))

        if len(line) > len_th:
            texts = []
            prev_begin = 0
            delimiters = ".!?;:"
            for i, c in enumerate(line):
                if (c in delimiters and i - prev_begin > len_th) or i == len(line) - 1:
                    texts.append(line[prev_begin : i + 1])
                    prev_begin = i + 1
        else:
            texts = [line]

        alpha = 2.0
        for text in tqdm(texts):
            time_s = perf_counter()
            mel = acoustic_model.forward(text, alpha=alpha, speaker_emb=speaker_emb)
            time_acoustic_model += perf_counter() - time_s

            time_s = perf_counter()
            audio = vocoder.forward(mel)
            time_vocoder += perf_counter() - time_s

            audio_res = np.append(audio_res, audio)

    total_latency = (perf_counter() - time_s_all) * 1e3
    log.info("Metrics report:")
    log.info("\tLatency: {:.1f} ms".format(total_latency))
    log.debug("\tVocoder time: {:.1f} ms".format(time_vocoder * 1e3))
    log.debug("\tAcoustic model time: {:.1f} ms".format(time_acoustic_model * 1e3))

    return (audio_res, total_latency)


def load_tts():
    global engine_ft_melgan
    log.debug("Loading ft + melgan model")
    engine_ft_melgan = load_tts_ft_melgan()

    global engine_glow_hifigan
    log.debug("Loading glow + HifiGAN model")
    engine_glow_hifigan = load_tts_glow_hifigan()


def tts_main(tts_model, speaker_id, text_data, alpha=1.0, gender="Male", style=1.0):
    log.debug("Inside tts_main")
    if tts_model == 1:
        log.debug("Inside tts_main_ft_melgan:")
        response = tts_main_ft_melgan(
            speaker_id,
            text_data,
            engine_ft_melgan[0],
            engine_ft_melgan[1],
            alpha,
            gender,
            style,
        )
    elif tts_model == 2:
        response = tts_main_glow_hifigan(
            speaker_id, text_data, engine_glow_hifigan[0], engine_glow_hifigan[1]
        )
    else:
        raise Exception("model not supported")
    return response


if __name__ == "__main__":
    sys.exit(main() or 0)
