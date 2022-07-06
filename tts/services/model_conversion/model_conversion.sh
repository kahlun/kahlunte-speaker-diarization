#!/bin/bash 

#sudo apt-get update 
#sudo apt-get install wget -y 
workdir=`pwd`
mkdir -p tmp/onnx
mkdir -p tmp/Model 
mkdir -p tmp/Repos 

model_dir=$workdir/tmp/Model
repo_dir=$workdir/tmp/Repos
conv_onnx_dir=$workdir/tmp/onnx

cd $model_dir
## HifiGan 
wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1QEBKespXTmsMzsSRBXWdpIT0Ve7nnaRZ' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1QEBKespXTmsMzsSRBXWdpIT0Ve7nnaRZ" -O generator_v1 && rm -rf /tmp/cookies.txt

wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1l5EUVBKM0SK7ec4HWf_wZvEITAsdOLFC' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1l5EUVBKM0SK7ec4HWf_wZvEITAsdOLFC" -O config.json  && rm -rf /tmp/cookies.txt

# Glow TTS
wget --load-cookies /tmp/cookies.txt "https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id=1RxR6JWg6WVBZYb-pIw58hi1XLNb5aHEi' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id=1RxR6JWg6WVBZYb-pIw58hi1XLNb5aHEi" -O pretrained_blank.pth && rm -rf /tmp/cookies.txt
 
cd $repo_dir
## Clone github repos for vocoder and acoustic 
git clone https://github.com/jik876/hifi-gan.git 
git clone https://github.com/jaywalnut310/glow-tts.git

cd $workdir


# Copying the conversion scripts 

cp hifi_gan_to_onnx.py $repo_dir/hifi-gan/.
#cp config.json tmp/Repos/hifi-gan/.
cp tts-glow-conversion.py $repo_dir/glow-tts/. 


# Conversion 
cd $repo_dir/hifi-gan
python3 hifi_gan_to_onnx.py --checkpoint_file $model_dir/generator_v1 --onnx_file $conv_onnx_dir/LJ_FT_T2_V1.onnx


## Covert glow-tts to onnx 

cd $repo_dir/glow-tts
cd monotonic_align && python3 setup.py build_ext --inplace
cd - && python3 tts-glow-conversion.py 
cp glow-tts-blank.onnx $conv_onnx_dir/.

# Copy the converted model 
cd $workdir
mkdir -p Model_onnx
cp -r $conv_onnx_dir/* Model_onnx/.
 
rm -rf tmp 


## openvino IR conversion 

mkdir ../model_openvino
mo --input_model Model_onnx/LJ_FT_T2_V1.onnx --output_dir ../model_openvino/
mo --input_model Model_onnx/glow-tts-blank.onnx --output_dir ../model_openvino/
rm -rf Model_onnx




