# Verified GitHub artwork delivery

Artifact commit: `c1c52d07e6ab4cae0c99c91701448ad0aa5a88a7`.

Branch: `review/publication-masters-ijdrs-20261111`.

The push completed successfully. Git LFS reported 37 uploaded objects (264 MB); the additional historical companion payload was already present. The local artifact commit and `git ls-remote` branch HEAD matched before retrieval verification.

`REMOTE_DELIVERY.json` records complete HTTP downloads of all 38 changed LFS payloads, totaling 269,050,417 bytes. Each download passed SHA256, byte-count and PDF/PNG/TIFF signature checks against the committed LFS identity. Pointer-file existence was not used as a substitute.

`ORIGINAL_LINK_AVAILABILITY.json` separately records successful HEAD availability checks for the 32 unchanged master PDF/PNG files and three original reading packets. These are availability checks, not a claim that the originals were redundantly downloaded and rehashed remotely. Their local payload hashes independently match the frozen starting Git LFS OIDs.

This receipt and the two JSON records are a documentation-only follow-up commit. They inherit the verified artifact commit without changing its artwork. The final branch HEAD must be checked again after pushing the receipt. No merge, force-push or source-branch update is performed.

The original source worktree remains at `68c83459e60ef31f7e86af9155d5a11e1680235d`, with its same three pre-existing untracked entries and no staged changes. All 32 numbered master payloads are unchanged. Preservation scope and the unavailable portion of the old 950-file inventory are explicitly documented rather than overstated.

Reproduction:

```powershell
python src/la_grid/plotting/publication_artwork.py build
python -m pytest tests/test_publication_artwork_20261111.py -q
python results/publication_artwork_20261111/verify_remote_payloads.py --commit HEAD --output results/publication_artwork_20261111/tmp/remote_recheck.json
```

The last command downloads the changed remote payloads again and is optional for collaborators who already trust the recorded hashes. It does not upload new artifacts.
