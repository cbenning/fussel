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

WORKDIR /fussel

COPY requirements.txt /fussel/
RUN pip3 install -r requirements.txt

COPY docker/start.sh /
COPY fussel.py \
    generate_site.sh \
    LICENSE \
    README.md \
    .env.sample \
    /fussel/
COPY generator/ /fussel/generator/
COPY web/ /fussel/web/

WORKDIR /fussel/web/
RUN yarn install

CMD ["/start.sh"]
