# E theme provenance

## Retained collection for local workstation proof

`catalog/themes.json` records 23 retained desktop EDJs from the user's existing
theme collection, with individual hashes and `e-theme-*` APK names. These are
local proof assets, not newly compiled or declared E27-compatible. The original
three have known collection notices; redistribution provenance for the other
retained binaries remains unclassified. Preserve the source mirror/fork branch
model for rebuilding and fixing those themes, rather than treating master as
the complete collection. Packages install in `/usr/share/elementary/themes`.
The old `alpine-spin-themes` name remains a compatibility metapackage only.

User identified https://github.com/simotek/Enlightenment-Themes as a source of
many prior AUZiX themes. Added it to the Gitea source catalog so all branches
are retained locally, with a separate writable fork for AlpinE changes.

Verified master: 48b5a9b5957357acedba17c8f48d3b83a46d61fd, 2026-09-19.
This repository uses a branch per theme; master is the development base, not
the complete theme selection to install. Existing AUZiX assets named Dark,
Transient and Transient-Color have corresponding upstream branches. That is a
provenance lead, not yet a byte-for-byte identification of our retained EDJs.

Candidate branches to recover our previous look:
- Dark: 99d6e2d347a5490f7d47f427e58be0e609509eb3
- Transient: 36b93c543eb629c9c02e082114646dfca2430e6c
- Transient-Color: 04b14c8cb922d43c835e3bb11dbfcdb0451ff3ee
- anti-transient-color: eb87192f5b3ee12dba902168077905dbf65d7826

The top-level COPYING describes multiple licenses: EDC sources, images,
Terminology themes and build scripts have different notices. Carry COPYING
and the applicable licenses-authors notices with packaged themes. Do not label
the entire collection with one inferred license. Preserve author credits.

Build selected branches using their upstream tooling and our EFL tools, then
package EDJ assets under normal system theme directories. Do not run the
upstream home-directory installer as an APK install hook. Theme selection and
first-login defaults belong to AlpinE's theme/default packages, and must not
overwrite an existing user's customization. Check current E/Elementary and
Terminology rendering before making a theme the default.

## Additional candidate: chrisripp/Themes

User suggested https://github.com/chrisripp/Themes. Verified master commit
e3e26daaf59ae645a46229e49c2777a22bbc893c. Contains NightBlue.edj and a Retrowave
theme distributed as two split 7z parts. README describes NightBlue as derived
from the E23 default theme through Darkmod, with an oz-23 menu contribution.
Treat these as candidate visual references/assets, not confirmed E27 themes.
No standalone COPYING/LICENSE appeared in the inspected tree; source and
redistribution provenance remain to be established before release packaging.
Mirror/fork name: chrisripp-themes. No automatic default-theme selection.
