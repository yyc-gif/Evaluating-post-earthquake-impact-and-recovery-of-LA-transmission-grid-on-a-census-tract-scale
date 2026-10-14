# Approved Candidate A reproduction

This is a figure-only production layer. Do not run Stage 7, K-means, Monte Carlo,
source propagation, scheduling or GA to reproduce this figure suite.

## Sources

- Accepted suite: `8f2dcb3b9762137b9f2686609c34480334f5d44e`.
- Approved layout: `aa55131cc5455aca9e1a6dead98e8f0eb8944217`.
- Frozen NCV14/H2/K3: `0c5365cc39e2717e0fab4aa3b5d05b445d427eb6`.
- D3: `05a78645b17bf8de04326e54181f9db432d7186c`.
- S10 caption correction: `7795638a73ac533d544971c20db13cf6662d13d3`;
  explicitly carried forward without merging its branch.

Pinned Git objects and their actual LFS payloads are required. A default-branch
clone alone may not contain these source commits. Fetch the review branches and
the source commits before requesting a forced rebuild:

```powershell
git fetch origin review/official-figure-suite-ncv14-h2-k3-d3-20261013
git fetch origin review/figure7-scientific-layout-author-review-20261013
git fetch origin 0c5365cc39e2717e0fab4aa3b5d05b445d427eb6
git fetch origin 05a78645b17bf8de04326e54181f9db432d7186c
git lfs pull
git lfs fetch origin 8f2dcb3b9762137b9f2686609c34480334f5d44e
git lfs fetch origin aa55131cc5455aca9e1a6dead98e8f0eb8944217
git lfs fetch origin 0c5365cc39e2717e0fab4aa3b5d05b445d427eb6
git lfs fetch origin 05a78645b17bf8de04326e54181f9db432d7186c
```

The broad fetches above may download unrelated large diagnostic sources. For a
space-limited clone, use `--include` with the exact paths listed in
`SOURCE_AUTHORITY_AND_HASHES.json`. Source lookup validates SHA256 and size and
fails explicitly rather than substituting an old or partial figure.

## Production

Use Python 3.12 with the repository requirements and the existing figure-only
requirements. Arial and Arial Bold were obtained from Windows for this delivery;
fonts must be available at the generator's documented paths for exact replay.

```powershell
python -m pip install -r requirements.txt
python -m pip install -r docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/figure-requirements.txt
python src/la_grid/plotting/build_current_suite_k3.py --portable
python src/la_grid/plotting/build_current_suite_k3.py --portable --rebuild
python -m pytest tests/test_current_figure_suite_integration.py -q
```

Default replay checks both generator modules and every canonical output hash.
Forced replay regenerates the approved ECDFs and cohort-z heatmap from frozen
observations, copies the existing C/D vector region, and applies only authorized
N/A local paint overrides. It does not invoke the historical artwork layer.
The explicit `--historical-ncv14` option retains that earlier layer for historical
reproduction and must not be used for current production.

The local validation used `C:\Users\yinch\anaconda3\python.exe`. ReportLab was
provided through the bundled runtime's pure-Python site-packages, appended to
`sys.path` after Anaconda packages; no scientific package versions were replaced.
The bootstrap is recorded in `check_build_replay.py`. Two forced builds and two
default replays must retain identical canonical output bytes.

## Independent checks

```powershell
python docs/reproducibility/figure7_candidateA_approved_integration_20261013/verify_integration.py
python docs/reproducibility/figure7_candidateA_approved_integration_20261013/check_build_replay.py
```

The independent verifier additionally reads the manifest-bound original author
checkout to check all 950 protected files, its 862 staged files and Git index.
That author-local preservation check is not reproducible in a clean public clone;
the committed before/after records preserve its evidence. The numerical, ECDF,
profile, vector, packet and mirror checks use declared pinned Git/LFS sources.

On Windows, if the deep audit script path exceeds MAX_PATH, execute it through
`runpy.run_path` using a resolved `\\?\` path. The scripts normalize the workspace
root before invoking Git. Never replace a source-null measurement or rerun any
physical calculation to work around missing archived payloads.
