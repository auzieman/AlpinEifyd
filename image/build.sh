#!/bin/sh
set -eu
set -o pipefail
export ALPINE_REPOSITORY_URL=${ALPINE_REPOSITORY_URL:-https://auzix.auzietek.com/alpine/repo/v3.24}
: "${ALPINE_REPOSITORY_KEY:?Public APK signing key path}"
: "${OUTDIR:?Image output directory}"
image_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mode=${BOOT_MODE:-BIOS}
case "$mode" in BIOS|UEFI) ;; *) exit 2;; esac
mkdir -p "$OUTDIR"
test ! -e "$OUTDIR/alpine-$mode.img"
test ! -e "$image_dir/configure.complete"
python3 "$image_dir/gen-skeleton.py" alpine-live "$OUTDIR/skeleton"
install -m644 "$ALPINE_REPOSITORY_KEY" /etc/apk/keys/
mkdir -p /var/cache/alpine-image-apk
ln -sfn /var/cache/alpine-image-apk /etc/apk/cache
alpine-make-vm-image --version
alpine-make-vm-image --image-format raw --image-size 8G --partition \
    --boot-mode "$mode" --kernel-flavor lts --serial-console \
    --initfs-features 'ata scsi usb virtio nvme kms' \
    --keys-dir /etc/apk/keys \
    --repositories-file "$OUTDIR/skeleton/etc/apk/repositories" \
    --packages "$(cat "$image_dir/packages")" \
    --fs-skel-dir "$OUTDIR/skeleton" --fs-skel-chown root:root \
    "$OUTDIR/alpine-$mode.img" "$image_dir/configure-host.sh" \
    2>&1 | tee "$OUTDIR/native-image.log"
# Some upstream cleanup paths return zero after a failed customization hook.
test -s "$image_dir/configure.complete"
grep -q '> Completed' "$OUTDIR/native-image.log"
cp "$image_dir/configure.complete" "$OUTDIR/configure.complete"
qemu-img info "$OUTDIR/alpine-$mode.img"
sha256sum "$OUTDIR/alpine-$mode.img" > "$OUTDIR/alpine-$mode.img.sha256"
printf 'RAW IMAGE COMPLETE: %s/alpine-%s.img\n' "$OUTDIR" "$mode"
