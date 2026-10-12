#!/bin/sh
set -eu
mkdir -p "$HOME/.abuild" /work/aports
if [ ! -f "$HOME/.abuild/abuild.conf" ]; then
    abuild-keygen -a -i -n
fi
sudo cp "$HOME"/.abuild/*.pub /etc/apk/keys/
cp -R /recipes/. /work/aports/
# Fetch/check every source before compilation. Native abuild reuses SRCDEST.
while IFS= read -r name; do
    (cd "/work/aports/$name" && abuild fetch verify)
done < /build-order
while IFS= read -r name; do
    cd "/work/aports/$name"
    if [ -f .build-complete ]; then
        echo "REUSE: $name from this exact compiler/recipe image"
    else
        echo "BUILD: $name"
        abuild -r
        touch .build-complete
    fi
    if ! grep -qxF /packages/aports /etc/apk/repositories; then
        printf '/packages/aports\n' | sudo tee -a /etc/apk/repositories > /dev/null
    fi
done < /build-order
for apk in /packages/aports/*/*.apk; do apk verify "$apk"; done
echo 'COMPLETE: signed native APKs in /packages/aports; desktop runtime validation follows separately.'
