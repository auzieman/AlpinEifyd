FROM alpine:3.24.2@sha256:d56c381f961d307a21b3ca004cf1e3910f106644aefb1f43e654c8a56c4fd395
RUN apk add --no-cache alpine-make-vm-image python3 qemu-img qemu-tools \
    rsync util-linux e2fsprogs dosfstools eudev flatpak
COPY image/ /image/
ENTRYPOINT ["sh", "/image/build.sh"]
