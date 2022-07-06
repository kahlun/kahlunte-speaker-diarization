TAG:=1.0

build:
	rm -rf va_bot.tar
	cp -r ../config/ .
	cp -r ../../../protos/ .
	docker build -t voice-announcement-bot-eii:${TAG} -f voice_announcement_bot_eii.dockerfile .
	rm -rf config
	rm -rf protos

run:
	docker-compose -f voice_announcement_bot_eii_compose.yml up

stop:
	docker-compose -f voice_announcement_bot_eii_compose.yml down

save:
	rm -rf va_bot.tar
	docker save -o va_bot.tar voice-announcement-bot-eii:${TAG}

del:
	rm -rf va_bot.tar

all: build run
