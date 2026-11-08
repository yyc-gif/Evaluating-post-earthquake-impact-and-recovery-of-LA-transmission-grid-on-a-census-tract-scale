# S5 cutoff labels - 2026-11-07

Baseline: `56bace172c5af1891d12cf6f7fde8735a334a431`.

Replace the two visible uses of internal workflow terminology:

- `3% production` becomes `3% cutoff`.
- The vertical axis becomes `Change from 3% cutoff (h)`.

The 3% cutoff remains the same zero reference. Point values, selected-cutoff
annotation, curves, scales and panels B/C are unchanged. Original Arial font
sizes and label centers are retained. The source's clipped vector labels are
omitted using vector clipping, avoiding shared-text-stream redaction artifacts.

`mapping_cutoff_labels` in `figure_presentation.py` is now called by the current
canonical suite builder. Pinned historical generators and internal identifiers
remain unchanged. Current figures cannot recover the old visible labels on
rebuild. No statistical quantity or physical simulation is recalculated.

`QA.json` records both label replacements, exact source/output hashes, native
pixel identity outside the label areas, a text audit of all sixteen numbered
figure PDFs, deterministic replay, and the thirty unchanged artwork hashes.
The current S5 PDF/PNG, mirror, preview, manifests and supplementary/complete
packets are synchronized. The main-figure packet and captions are unchanged.

```powershell
& C:\Users\yinch\anaconda3\python.exe docs/reproducibility/s5_cutoff_wording_20261107/refresh.py
& C:\Users\yinch\anaconda3\python.exe -m pytest -p no:cacheprovider tests/test_s5_cutoff_wording_20261107.py -q
```
