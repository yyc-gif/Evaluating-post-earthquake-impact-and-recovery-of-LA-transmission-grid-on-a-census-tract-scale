# RQ-Aligned Figure Suite Review

This is an isolated figure-only review build from baseline `1887bca4872f24d6d547637440db5619a4423452`. It does not replace the approved suite, change manuscript files, or modify model and simulation results.

## Suite and RQ coverage

The packet contains 7 main figures and 9 supplementary figures (16 pages total). Figure 1 is the workflow overview. Figures 2-3 support RQ1 on network/mapping, earthquake damage, and unconstrained service recovery. Figures 4-6 support RQ2 on restoration-strategy outcomes, distributional changes, and resource dependence. Figure 7 supports RQ3 with the seven-variable P2/K3 profiles, geography, and descriptive recovery-burden/social-vulnerability context.

The supplementary figures provide supporting evidence on initial damage (S1), task travel (S2), dynamic functional-network recovery (S3), GA search and separate validation evidence (S4), functionality/source assumptions (S5-S6), capacity context (S7), priority construction (S8), and scenario robustness (S9).

## Artwork changes

Six of 16 numbered figures changed: Fig01, Fig04, Fig05, Fig07, FigS03, and FigS08. The other ten numbered PDF/PNG pairs match the baseline SHA256 values in `FIGURE_CHANGE_MANIFEST.csv` exactly. Figure 4A remains the saved vector artwork because the archived event-history arrays needed for a faithful reconstruction were unavailable; no trajectory was interpolated. Figure 7 uses saved P2/K3 results and verified overlap inputs; it is descriptive and policy-conditioned, not an external validation or a causal hotspot claim.

For Figure 7, the verified cohort is 2,299 positive-population tracts and 9,066,522 residents, with K3 counts 1,235 / 428 / 636. Sixteen zero-population tracts remain N/A; the eight positive-population zero-housing tracts remain classified. The descriptive Q4/P75 intersection is 94 tracts and 350,799 residents at 38.38135467381475 equivalent deficit hours.

## Verification

- Canonical portable builder ran twice; second-run output hashes matched (`second_run_hashes_match=true`, `second_run_pending=false`).
- Dedicated isolated-suite tests: 11 passed in 75.87 seconds.
- Packet PDFs contain 7 main pages, 9 supplement pages, and 16 combined pages. Each combined page contains one figure followed by its caption.
- Review mirrors match their authoritative review PDFs/PNGs by file hash.
- Native-size PDF pages and contact sheets were inspected. The smallest extracted figure text is approximately 6.8 pt; most text is 7 pt or larger. This is noted for final journal-specific layout review rather than represented as universally compliant.
- Preservation audit confirms all 23 registered scientific-source files available in this isolated worktree and all unrelated numbered artwork checked by the manifest are unchanged. This is not a claim that the separate historical 950-file inventory was available for a complete rehash.
- Figure 3 component additivity, Figure 4 paired outcome identities, and Figure 7 cohort/membership/screen counts are documented in the adjacent QA records.

## Limits and delivery state

These results are derived from frozen model outputs, not observed customer-outage data. Figure 4A could not be regenerated from unavailable event histories. The existing legacy integration test is tied to the official `results/figure_review/` paths and does not target this isolated output directory; the dedicated review tests and canonical double-build were used for this review output.

The review branch is separate from `1021` and the October 14 publication baseline. The remote branch lookup returned no matching branch and direct GitHub access failed with a DNS/thread-start error. Standard Git LFS staging failed in this isolated Windows worktree, so the final artifacts were encoded as verified Git LFS pointers using the local clean operation. The index contains 85 LFS file entries backed by 53 unique, locally verified payloads (267.72 MiB). Commit and remote delivery are pending; no remote upload is claimed here.

Rebuild command:

```powershell
python src/la_grid/plotting/build_current_figures.py --portable --output-dir results/figure_review_rq_aligned_20261101 --mirror-dir results/figures_rq_aligned_20261101
```
