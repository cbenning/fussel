FROM alpine:3.12

WORKDIR /fussel

COPY requirements.txt /fussel/

RUN apk add --no-cache python3 python3-dev py3-pip nodejs yarn sed bash \
        libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev libc-dev gcc \
    && pip3 install --no-cache -r requirements.txt \
    && apk del python3-dev py3-pip libjpeg-turbo-dev zlib-dev libc-dev gcc

COPY . /fussel

WORKDIR /fussel/web/
RUN yarn config set disable-self-update-check true \
    && yarn install \
    && rm -r /usr/local/share/.cache

WORKDIR /

COPY docker/start.sh /

CMD ["/start.sh"]
