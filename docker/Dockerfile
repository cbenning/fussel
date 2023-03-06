FROM alpine:latest

LABEL org.opencontainers.image.source=https://github.com/cbenning/fussel
LABEL org.opencontainers.image.description="A static photo gallery generator "
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /fussel

COPY . /fussel/

RUN apk add --no-cache curl jq yq python3 python3-dev py3-pip nodejs yarn sed bash && \
    apk add --no-cache libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev libc-dev gcc && \
    yarn config set disable-self-update-check true && \
    ./setup.sh && \
    apk del python3-dev py3-pip libjpeg-turbo-dev zlib-dev libc-dev gcc && \
    rm -r /usr/local/share/.cache

WORKDIR /

COPY docker/start.sh /

CMD ["/start.sh"]
