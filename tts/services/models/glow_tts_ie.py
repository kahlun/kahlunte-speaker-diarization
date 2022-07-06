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

import logging as log
import os.path as osp

import numpy as np
from openvino.runtime import PartialShape

from utils.text_preprocessing_hifi import (
    text_to_sequence_with_dictionary,
    intersperse,
    seq_to_text,
)
import utils.cmudict as cmudict


def check_input_name(model, input_tensor_name):
    try:
        model.input(input_tensor_name)
        return True
    except RuntimeError:
        return False


class GlowTTSIE:
    def __init__(self, model_path, ie, device="CPU", verbose=False):
        self.verbose = verbose
        self.device = device
        self.ie = ie

        self.cmudict = cmudict.CMUDict(
            osp.join(osp.dirname(osp.realpath(__file__)), "data/cmu_dictionary")
        )

        self.net = self.load_network(model_path)
        self.input_data_name = "x_tst"
        self.input_mask_name = "x_tst_lengths"
        self.length_scale_name = "length_scale"
        self.noise_scale_name = "noise_scale"

        new_shape = {
            self.input_data_name: PartialShape([1, -1]),
            self.input_mask_name: PartialShape([1]),
            self.length_scale_name: PartialShape([1]),
            self.noise_scale_name: PartialShape([1]),
        }
        self.net.reshape(new_shape)
        self.net_request = self.create_infer_request(self.net, model_path)

    def seq_to_indexes(self, text):
        res = text_to_sequence_with_dictionary(text, self.cmudict)

        if self.verbose:
            log.debug(res)
        return res

    def load_network(self, model_xml):
        model_bin_name = ".".join(osp.basename(model_xml).split(".")[:-1]) + ".bin"
        model_bin = osp.join(osp.dirname(model_xml), model_bin_name)
        log.info("Reading GlowTTS model {}".format(model_xml))
        model = self.ie.read_model(model=model_xml, weights=model_bin)
        return model

    def create_infer_request(self, model, path=None):
        compiled_model = self.ie.compile_model(model, device_name=self.device)
        if path is not None:
            log.info("The GlowTTS model {} is loaded to {}".format(path, self.device))
        return compiled_model.create_infer_request()

    @staticmethod
    def sequence_mask(length, max_length=None):
        if max_length is None:
            max_length = length.max()
        x = np.arange(max_length, dtype=length.dtype)
        return np.expand_dims(x, 0) < np.expand_dims(length, 1)

    def preprocess(self, text):
        seq = self.seq_to_indexes(text)
        seq = intersperse(seq)

        seq = np.array(seq)[None, :]
        seq_len = np.array([seq.shape[1]])

        return {
            self.input_data_name: seq,
            self.input_mask_name: seq_len,
            self.noise_scale_name: np.array([0.333]),
            self.length_scale_name: np.array([1.0]),
        }

    def forward(self, text, **kwargs):
        input_data = self.preprocess(text)
        self.net_request.infer(input_data)
        res = self.net_request.get_tensor("mel").data[:]

        return res
