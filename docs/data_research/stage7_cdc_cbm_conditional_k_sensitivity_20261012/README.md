# Conditional CDC CBM review package
EXPLORATORY AUTHOR REVIEW — NOT FORMAL STAGE 7

Start with FINAL_CBM_CONDITIONAL_AUTHOR_DECISION.md. This package is an isolated author review; formal admission remains unresolved and no final model/K is promoted.

Starting source authority: `896d75d527325d8ea3ac408357cf4be7747e441e`. Reproduce with Python3.12 and repository dependencies after `git lfs pull`:

```powershell
python prepare.py --core-only
python fit_registered.py
python build_evidence.py
python reports.py
python figures.py
python verify_independent.py
```

Run from this directory or give full script paths. The source resolver verifies actual Git/LFS bytes and searches the current checkout and known archived worktrees. Core-only preparation explicitly skips external-archive preservation checks; use `python prepare.py` without that flag and set LA_GRID_FROZEN_SOURCE_ROOT to the manifest-bound original archive to perform the950-file/source-Git checks. `verify_independent.py` performs that full preservation verification and therefore requires the original archive. The diagnostic arithmetic/fits use tracked prior CDC/multi-policy extracts; raw event reproduction still needs external archives. A clean clone can reproduce the core results, but cannot substantiate the unavailable original archive by inference.

Main K1–8: P2,H1,H2,seeds42–46,n_init50,Lloyd,max_iter500,tol1e-4. Component removals: national83,509, H1/H2 K3–5,seeds42–46. Policy/geographic: K2–8,seed42, documented cohort and fixed-reference/training-only scaling. Init ablation:K3–5,seed42 with RQ1 redistribution. No MC/GA/recovery code is invoked. WCSS is weighted-space within-cluster sum of squares.

Full labels, silhouettes, matrices and prediction arrays are LFS NPZs. All publication-size vector PDFs and600dpi previews are under figures/. Matplotlib/GeoPandas generate the figures; no AI-generated artwork. Every component-removal rank is a researcher diagnostic, not an official CDC replacement. PER_CLUSTER_CBM_AND_RQ_PROFILES distinguishes researcher_climate_rank from Published_RPL_CBM. CSV IDs are model-specific, not formal Stage7 IDs.

Numerical QA, source hashes, preserved-science checks and remote real-LFS-byte verification are recorded separately. CDC_EJI_TECHNICAL_CLARIFICATION_DRAFT.md is draft-only. Source/provider license terms remain those in the original repository and CDC audit; no third-party data is re-licensed here.
