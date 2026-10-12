FROM alpine:3.24.2@sha256:d56c381f961d307a21b3ca004cf1e3910f106644aefb1f43e654c8a56c4fd395
RUN apk add --no-cache alpine-sdk sudo python3 && \
    adduser -D -u 1000 builder && addgroup builder abuild && \
    printf 'builder ALL=(ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/builder
COPY aports/ /recipes/
ARG BUILD_ORDER=order
COPY build/${BUILD_ORDER} /build-order
COPY build/prepare-dependencies.sh /usr/local/bin/prepare-dependencies
RUN sh /usr/local/bin/prepare-dependencies
COPY build/build-packages.sh /usr/local/bin/build-packages
ENV HOME=/home/builder JOBS=5 MAKEFLAGS=-j5 REPODEST=/packages SRCDEST=/var/cache/distfiles
USER builder
WORKDIR /work
ENTRYPOINT ["sh", "/usr/local/bin/build-packages"]
