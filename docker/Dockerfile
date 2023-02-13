FROM alpine:latest

WORKDIR /fussel

# COPY requirements.txt /fussel/
COPY . /fussel/

RUN apk add --no-cache curl jq yq python3 python3-dev py3-pip nodejs yarn sed bash \
        libjpeg-turbo libjpeg-turbo-dev zlib zlib-dev libc-dev gcc \
    && ./setup.sh \
    # && pip3 install --no-cache -r requirements.txt \
    && apk del python3-dev py3-pip libjpeg-turbo-dev zlib-dev libc-dev gcc \
    && rm -r /usr/local/share/.cache
RUN yarn config set disable-self-update-check true 

COPY . /fussel

#WORKDIR /fussel/web/
#RUN yarn config set disable-self-update-check true \
#    && 
#    && yarn install \
#    && rm -r /usr/local/share/.cache

WORKDIR /

COPY docker/start.sh /

CMD ["/start.sh"]
