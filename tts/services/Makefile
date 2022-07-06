TAG:=1.0
build: 
	cp -r ../protos/ .
	cp -r ../openvino_installation_files/ .
	docker build -f tts.dockerfile -t tts:${TAG} .
	rm -rf protos
	rm -rf openvino_installation_files
run: 
	docker-compose -p tts -f tts-docker-compose.yml up 
stop:
	docker-compose -p tts -f tts-docker-compose.yml down       	
all: build run
