# Pinned so builds are repeatable. Dependabot opens PRs for new versions.
FROM ghcr.io/astral-sh/uv:0.13.10 AS uv

FROM alpine:3.24

LABEL org.opencontainers.image.source=https://github.com/cbenning/fussel
LABEL org.opencontainers.image.description="A static photo gallery generator "
LABEL org.opencontainers.image.licenses=MIT

WORKDIR /fussel

COPY --from=uv /uv /uvx /usr/local/bin/
COPY . /fussel/

RUN apk add --no-cache curl jq yq python3 python3-dev nodejs npm sed bash make imagemagick libheif libheif-tools libheif-plugins-all && \
    apk add --no-cache libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev libc-dev gcc && \
    make install build-web && \
    apk del python3-dev libjpeg-turbo-dev zlib-dev libc-dev gcc && \
    rm -rf /root/.npm /root/.cache

WORKDIR /

COPY docker/start.sh /
COPY docker/generate_config.sh /
COPY docker/template_config.yml /

CMD ["/start.sh"]
