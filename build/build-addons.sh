#!/bin/sh
set -eu
cp /home/builder/.abuild/*.pub /etc/apk/keys/
printf '/packages/aports\n' >> /etc/apk/repositories
sh /usr/local/bin/prepare-dependencies
exec su builder -s /bin/sh -c 'sh /usr/local/bin/build-packages'
