FROM alpine:3.11.6

RUN apk add --no-cache \
	python3 \
	py3-pillow \
	py3-pip \
	nodejs \
	yarn \
	git	\
	sed \
	bash

COPY docker/start.sh /

WORKDIR /fussel
COPY fussel.py \
    generate_site.sh \
    LICENSE \
    README.md \
    requirements.txt \
    .env.sample \
    /fussel/
COPY generator/ /fussel/generator/
COPY web/ /fussel/web/

RUN pip3 install -r requirements.txt

WORKDIR /fussel/web/
RUN yarn install

CMD ["/start.sh"]
