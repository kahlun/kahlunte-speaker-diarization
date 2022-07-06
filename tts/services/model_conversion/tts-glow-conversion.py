from text.symbols import symbols
import models
import utils
import torch
import commons
from text import text_to_sequence, cmudict
import numpy as np

hps = utils.get_hparams_from_file("./configs/base_blank.json")
checkpoint_path = "../../Model/pretrained_blank.pth"
model = models.FlowGenerator(
    len(symbols) + getattr(hps.data, "add_blank", False),
    out_channels=hps.data.n_mel_channels,
    **hps.model
).to("cpu")
utils.load_checkpoint(checkpoint_path, model)
with torch.no_grad():
    model.decoder.store_inverse()
    _ = model.eval()
    cmu_dict = cmudict.CMUDict(hps.data.cmudict_path)
    tst_stn = "Glow TTS is really awesome !"
    if getattr(hps.data, "add_blank", False):
        text_norm = text_to_sequence(tst_stn.strip(), ["english_cleaners"], cmu_dict)
        text_norm = commons.intersperse(text_norm, len(symbols))
    else:  # If not using "add_blank" option during training, adding spaces at the beginning and the end of utterance improves quality
        tst_stn = " " + tst_stn.strip() + " "
        text_norm = text_to_sequence(tst_stn.strip(), ["english_cleaners"], cmu_dict)
    sequence = np.array(text_norm)[None, :]
    print("".join([symbols[c] if c < len(symbols) else "<BNK>" for c in sequence[0]]))
    x_tst = torch.autograd.Variable(torch.from_numpy(sequence)).cpu().long()
    x_tst_lengths = torch.tensor([x_tst.shape[1]]).cpu()
    noise_scale = torch.tensor(0.333, dtype=torch.float32)
    length_scale = torch.tensor(
        1.0, dtype=torch.float32
    )  # (y_gen_tst, *_), *_, (attn_gen, *_) = model(x_tst, x_tst_lengths, gen=True, noise_scale=noise_scale,
#                                             length_scale=length_scale)
# torch.onnx.export(model.encoder, f="glow-tts_encoder.onnx",
#                   args=(x_tst, x_tst_lengths),
#                   input_names=['x_tst', 'x_tst_lengths'],
#                   # dynamic_axes={'input.1': {0: 'seq_len', 1: 'batch'}},
#                   opset_version=12)
torch.onnx.export(
    model,
    f="glow-tts-blank.onnx",
    args=(x_tst, x_tst_lengths, None, None, None, True, noise_scale, length_scale),
    # args=(x_tst, x_tst_lengths),
    # input_names=['x_tst', 'x_tst_lengths', 'gen', 'noise_scale', 'length_scale'],
    input_names=["x_tst", "x_tst_lengths", "", "noise_scale", "length_scale"],
    output_names=["mel"],
    dynamic_axes={"x_tst": {1: "seq_len"}},
    opset_version=12,
)
