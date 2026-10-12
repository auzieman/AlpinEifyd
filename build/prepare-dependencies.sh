#!/bin/sh
set -eu
# Native recipe metadata is the dependency authority. All external build inputs
# are installed into the reusable compiler image before any package compiles.
while IFS= read -r name; do
    (
        cd "/recipes/$name"
        # APKBUILD is sourced by abuild without nounset; srcdir and other native
        # build-context variables need not exist for this metadata-only read.
        set +u
        . ./APKBUILD
        printf '%s\n' "$pkgname" ${subpackages:-} | cut -d: -f1
    )
done < /build-order | sort -u > /tmp/local-package-names
while IFS= read -r name; do
    (
        cd "/recipes/$name"
        set +u
        . ./APKBUILD
        printf '%s\n' ${depends:-} ${makedepends:-} ${checkdepends:-}
    )
done < /build-order | sort -u | grep -v -x -F -f /tmp/local-package-names > /tmp/external-build-dependencies
apk add --no-cache $(cat /tmp/external-build-dependencies)
apk info -v > /compiler-package-inventory.txt
