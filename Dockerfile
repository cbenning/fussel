FROM alpine:3.11.6

RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    nodejs \
    yarn \
    git	\
    sed \
    bash \
    libjpeg-turbo \
    libjpeg-turbo-dev \
    zlib \
    zlib-dev \
    libc-dev \
    gcc

COPY requirements.txt /fussel/

WORKDIR /fussel

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

WORKDIR /

CMD ["/start.sh"]
