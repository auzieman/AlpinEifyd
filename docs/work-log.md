# Public work log

## 2026-10-12 — GitHub source publication

User created auzieman/AlpinEifyd and authorized source publication and companion links. Prepare a scoped source snapshot from the native AlpinE checkout, retaining the current installer and package selection. Preserve the private checkout and its working changes. Exclude local installation plans, credentials, outputs, lab receipts and unresolved third-party EDJ binaries. Keep recipe provenance and document build prerequisites. Publish through SSH; no browser or desktop restart.

Rollback: revert the public publication commit; existing signed package feeds and media are not modified. Validation and publication results follow.

Validation: all ten shared E’ifyd installer unit tests pass. Source snapshot preserves copied-file hashes; build outputs and third-party EDJ files are excluded. No new APK compilation, image boot or physical installation is claimed.

## 2026-10-12 — Public GitHub companion links

Published the scoped source preview at https://github.com/auzieman/AlpinEifyd through SSH. E-Jamz and BlackKnight theme READMEs now cross-link the projects and walkthrough. BKC alpine-project-links run e7a9c0f7-ee2b-46af-9679-86c64a0a6092 completed; both public AUZiX and AlpinE homepages verified HTTP 200 with all three repository links and the walkthrough. Existing media and APK feed retained. No browser, build or desktop restart used. Public snapshot validation: ten installer unit tests pass, Python/JSON/shell checks and credential scan pass. Theme binaries with unresolved per-asset notices are excluded; the full public-order build needs verified theme inputs.

Publication result: signed ejamz 0.1.0-r0 and blackknight-wallpapers 0.1.0-r0 are published at https://auzix.auzietek.com/alpine/repo/apps/v3.24/. BKC validation run 490909fd-80e2-4c31-aa0a-c38dfbdac8b8 and publication run cc54ba45-4cdb-4c97-9c05-4400a4e34984 completed. Native APK signatures, a clean-root installation, installed launcher/skin/wallpaper checks, musl ELF linkage, HTTPS byte hashes and fresh-client signed-index/package resolution passed. Both wallpaper EDJs match the accepted release bytes. The additional public key and fingerprint are documented in AlpinEifyd/docs/companion-apks.md; the private signer is retained on edge outside Git and public directories. Existing base-feed trust remains unchanged.

The native companion apps article and two related discussion articles are published; both AUZiX/AlpinE homepages include installation links. No runtime restart, laptop installation or new boot-image acceptance is claimed.
