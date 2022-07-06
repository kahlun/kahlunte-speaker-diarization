# Voice Announcement Bot EII

<img src=architecture_diagram.png>
<br></br>

## Install the required dependencies to run the voice-announcement-bot
```
python3 -m pip install -r requirements.txt
```
<br></br>

 Key                 | Value                                                                                         | Default Value   
---------------------|-----------------------------------------------------------------------------------------------|-----------------
 default_device      | Default playback device ID                                                                    |                 
 block_input         | Block thread until all tasks are done                                                         | `True`            
 speaker_id          | Speaker ID                                                                                    | `19`              
 device              | CPU or GPU                                                                                    | `CPU`             
 alpha               | Coefficient for controlling of the speech time (should be greater than 0.5 and less than 2.0) | `1.0`             
 tts_server_endpoint | TTS Engine Endpoint                                                                           | `localhost:50052` 
 samplerate          | Sampling rate (Frames per second)                                                             | `16000`           
 ZMQ_TYPE            | ZMQ Type to be used ("zmq_ipc", "zmq_tcp")                                                    | `zmq_tcp`         
 ZMQ_HOST_IP         | Address/IP of the ZMQ server for the client to establish communication                        | `127.0.0.1`       
 ZMQ_HOST_PORT       | Port of the ZMQ server to which the client will connect/bind                                  | `3000`            
 ZMQ_TOPIC           | ZMQ Topic to enable pub/sub communication between clients                                     | `tts_zmq_topic`   
<br></br>


## To start the voice-announcement-bot-eii server
### The environment variables can also be modified from the code
```
block_input="False" speaker_id="19" device="CPU" alpha="1.0" tts_server_endpoint="localhost:30009" python3 voice-announcement-bot.py
```
<br></br>

## To run the voice-announcement-bot-eii as a Docker service
### Build the voice-announcement-bot-eii image
```
make build
```

### Run the voice-announcement-bot-eii image
### Take note to modify the environment variables in the docker-compose
```
make run
```
### Stop the voice-announcement-bot-eii service
```
make stop
```
<br></br>

## To run the voice-announcement-bot-eii as a Kubernetes service
### Build the voice-announcement-bot-eii image
```
make build
```

### Deploy the voice-announcement-bot-eii onto an existing k8s cluster
### Make the necessary changes to the environment variables in voice_announcement_bot_eii_k8s.yml
```
kubectl apply -f voice_announcement_bot_eii_k8s.yml
```
### Delete the voice-announcement-bot-eii from an existing k8s cluster
```
kubectl delete pod <voice-announcement-bot_podname>
```
