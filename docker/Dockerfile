FROM alpine:latest

LABEL org.opencontainers.image.source=https://github.com/cbenning/fussel
LABEL org.opencontainers.image.description="A static photo gallery generator "
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /fussel

COPY . /fussel/

RUN apk add --no-cache curl jq yq python3 python3-dev nodejs yarn sed bash make && \
    apk add --no-cache libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev libc-dev gcc && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    yarn config set disable-self-update-check true && \
    PATH="/root/.local/bin:$PATH" make install && \
    apk del python3-dev libjpeg-turbo-dev zlib-dev libc-dev gcc && \
    rm -rf /usr/local/share/.cache /root/.cache

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /

COPY docker/start.sh /
COPY docker/template_config.yml /

CMD ["/start.sh"]
