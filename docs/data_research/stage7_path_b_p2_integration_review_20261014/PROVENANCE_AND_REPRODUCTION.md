# Exact source authority and reproduction

| Purpose | Immutable commit |
|---|---|
| Latest source suite and continuous supplement numbering | `5fbdf5a33cb8cee4790f81e896776b8b6fb4f9ae` |
| Concise captions, unchanged numbered artwork | `21cf3d0` (full SHA in Git history) |
| P2 matrices, labels, physical pairing and policy integrals | `81c3452e29abc109f50564d39035c06225e3ea84` |
| Direct co-occurrence, full geometry and policy/geographic comparisons | `05a78645b17bf8de04326e54181f9db432d7186c` |
| NCV14 vector, components and final source limitations | `0c5365cc39e2717e0fab4aa3b5d05b445d427eb6` |
| Williams/FEMA method audit and normalization sensitivities | `49cc153c3f4d7a8c29cf94baf090dbfc0be4d068` |
| Exact 34-tract Q-linked reference | `66d16d61b13c05785f58795ef9d13ba82ece472e` |

`SOURCE_PAYLOAD_HASHES.csv` and `RARE_Q_SOURCE_HASH.csv` contain exact source paths, actual-byte SHA256s and acquisition records. Source documents are copied byte-for-byte. No CSV pointer is parsed as scientific data. Derived hashes and every generated path are in `OUTPUT_FILE_MANIFEST.csv`.

## Compact-input reproduction

Use Python 3.12 with NumPy, Pandas, SciPy, scikit-learn, GeoPandas, Matplotlib, Pillow, PyMuPDF, ReportLab and tabulate. Actual package versions are recorded in `REPRODUCTION_ENVIRONMENT.json`. `--archived-inputs` verifies the compact archived payload hashes instead of requiring the prior branches' local LFS cache. No original dirty worktree is required for scientific arithmetic/figure reproduction in this mode; live preservation is explicitly not rechecked.

```text
python analyze_path_b.py --archived-inputs
python make_review_figures.py
python independent_qa.py --archived-inputs
```

Run from the package directory or pass the repository-relative script path. On Windows, if the long workspace path exceeds Python's ordinary file-opening limit, use `runpy.run_path('\\?\' + os.path.abspath(script), run_name='__main__')`. The scripts handle long input/output paths internally. `run_review.ps1` records the tested command sequence and appends the optional bundled ReportLab dependency path only after the Anaconda packages, avoiding a NumPy ABI change.

Default source mode additionally validates pinned Git objects and live preservation. The 34-tract source is read from a retained interpretation checkout only when its bytes match the original Git LFS OID exactly. That exact payload is also archived here, so archived-input reproduction does not depend on the retained checkout.

The seven-variable scientific matrices and source integrals are reproducible from these compact inputs. Reconstructing all original exact-event trajectories still requires the manifest-bound external frozen archive; no full physical clean-clone run or new event integration is claimed. This review independently projects frozen station integrals through the exact stored mapping, checks all 1,000 physical identities and verifies saved labels. K-means is never called.

## Earlier prose versus saved stability records

The earlier multi-policy narrative's summarized P2/K3 leave-one-policy-out upper bound is not the range of the five saved seed42 partitions. Recomputing label-invariant ARI from the archived label arrays gives 0.618660-0.791635 at seed42, including the 0.791635 Degree-first omission. The source CSV and array agree. K4's corresponding seed42 range is 0.572174-0.809387. These scope-specific values are used here; earlier reports remain unchanged. Seed42 ranges must not be mixed with across-seed minima or averages.

The frozen P75 is 38.38135467381475 h. The independent arithmetic yields 38.38135467381474 h, a floating-point difference below 1e-13 h, with identical 575 selected tracts and the exact original 94 joint GEOIDs. No threshold formula or eligibility change is hidden by rounding.
