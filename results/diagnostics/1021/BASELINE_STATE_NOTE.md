# Baseline state and noninterference

The initial clean `2026-10-14` check and remote query identified final integrated
commit `b307e6deafc054864787a3db63ad95218be91659`. Branch 1021 was created from
that commit. Protocol commit `e10957e0f96be5d80c1e7d4781a84e52afcb6d6b` was
pushed before any substantive experiments.

The subsequent preflight deliberately stopped on an unexpected original-
worktree change. The old complete packet appeared deleted and a new untracked
`PowerGridRestoration_Figures_20261014_YY_YL_MG.pdf` appeared. Its actual SHA256
is `ad31b9373a43ced979ad0bcb43ac03566f19e5b1ac3be42cae532901037a1616`, exactly
the original committed packet's LFS object, with the same 80,342,847 bytes.
Remote October 14 HEAD remained b307e6de. No scientific or PDF-content delta
was present. This external filename-only change is not incorporated, staged,
committed, reverted or otherwise modified by 1021. The original worktree is
therefore NOT claimed to be clean at the later preservation snapshot.

The frozen branch baseline remains the verified pushed commit, not an
uncommitted filename. FROZEN_INPUT_REGISTRY.json records the actual later
source status and index identity for before/after noninterference checks.
There is no assertion that an untracked rename was delivered remotely.

This clarification does not change any preregistered experiment, numerical
criterion or computational budget. It and the verified input registry are
committed and pushed before substantive experiments as well.
