# Numerical and visual QA: final pure-random GA S05

## Scope And Identity Gates

**PASS.** All five requested local/remote evidence identities were inspected; the protected revision HEAD and remote manuscript HEAD are distinct and recorded. Source content is immutable Git content or actual hash-verified LFS bytes, not pointer text. The manifest enumerates 86 sources and the 3,865,728-byte lossless `SOURCE_EVIDENCE.zip` reproduces every archived source hash. This archive is sufficient to reconstruct plotted values, chosen-seed evidence, original candidate, saved CIs and equity qualification without executing archived search or simulation scripts.

The finalized configuration is exactly pop100/random100/OX0.80/swap0.10/tournament3/legacy elite1, 20 seeds, 100k distinct evaluations, 64 planning realizations. Every saved pool is valid and entirely random-only; the chosen permutation has 92 unique required IDs and the required `edc4ad19...bbfeb99a` hash. Its recorded loss and all64 production-parity receipt are reused unchanged. Original selection from the 20 main100k receipts reproduces seed 2026103108; reserved continuations, controls and validation outcomes are excluded.

## Numerical Checks

- All 20 runs finish exactly 100,000 distinct evaluations. No checkpoint is counted as another run.
- All 7,480 actual strict improvements at or below 100k are preserved; 20 final receipt points extend the existing archive unchanged to the budget boundary. Panel A starts after the 100 initial random orders, whose evaluations remain in the total budget. Initial and final values match original receipts exactly. No values are linearly interpolated.
- Pointwise median is computed from observed right-continuous histories at their union of actual improvement clocks, plus 100 and 100,000. It is a descriptive summary of 20 searches, not new optimizer evidence or inference.
- Initial best range 35.238959152796234-36.86557494743389 h; final range 32.99552241352315-33.00366101919527 h. Chosen initial best 36.08101107593356 h; search gain 3.0854886624104125 h is not inherited from an incumbent.
- Exactly 2,000 unique same-state GA/Impact pairs, identical realization-ID ordering and physical state hashes. Horizon 480 h in every case. Later corrected-elitism cohort excluded.
- Paired mean -0.5326745400470683 h; saved simultaneous95 CI [-0.5639820386601612,-0.5023213152613648] h; 1,741 improved, 259 worsened, 0 ties. Full distribution preserved with both tails. CIs copied from original two-contrast analysis, no bootstrap rerun.
- Same-cohort mean components: +0.27747545367176646 self, +0.010637992790297883 threshold, -0.8207879865091324 source-path; net -0.5326745400470683 h. Maximum per-realization accounting closure discrepancy 3.730349362740526e-14 h.
- Equity tradeoff retained: mean absolute Q4-Q1 gap +0.23273315730244332 h; population-weighted tract Gini +0.009790332270076018. Signed gap is not substituted for absolute disparity.
- Existing order-independent planning completion-bound proof is archived: maximum bound 134.33255016512265 h across all 64 states, below 480 h; intact components all have Core sources. Original planning horizon 2855.2540131100995 h and its completion-bound equivalence are retained without a new evaluator call.
- Independent standard-library reconstruction tests verify all source hashes, full candidate, all seed endpoints, median curve, paired identities, complete effects, saved mean/CI and component closure. **3 tests passed, 0 failures/errors**; actual receipt is `ARCHIVED_RECONSTRUCTION_TEST_RESULTS.json`.

## Actual Visual And PDF Inspection

The latest proposed PDF was rendered and opened through both PyMuPDF 200 dpi and Poppler 150 dpi, at publication width 185 mm. Original official PNG/PDF and latest side-by-side comparison were opened. Final PNG is 600 dpi (4,370x4,204 pixels). Proposed PDF has one page, dimensions 184.999991x177.999999 mm, embedded Arial/Arial Bold, minimum 7.5 pt extracted text, **zero raster images**. All curve/bar/ECDF geometry is vector. PDF text bounds and Matplotlib canvas bounds show no clipping.

Visual review checked all 20 curves, chosen-seed diamonds, legends, original-unit axes, panel labels, inset/CDF separation, zero references, complete physical tails, threshold-bar visibility, D value-label spacing and page footer. Reliability notes no longer overlay search lines or lower titles. The comparison embeds both vector pages at 185 mm each; headings and footer explain different evidence, not different performance in a common experiment. No unrelated artwork was changed.

Nonzero A/B loss origins are explicitly labeled absolute hours and show the complete initial-to-final span on the same scale, without fine-scale magnification of final differences. The mean-CI inset is explicitly separate from the full physical-distribution axis. ECDF quantiles are not labeled confidence intervals. Cumulative loss is not an instantaneous outage or delivered power.

## Limitations And Honest Exceptions

Pure random was a post-data choice; 10/20 did not meet the registered 90% single-run standard. Seed curves do not establish global optimality. Panel B final points nearly overlap because their true spread is small; exact values are accessible in the source CSV. The figure does not claim fairness improvement, actual customer restoration, electrical capacity or universal GA superiority.

One initial extraction attempt failed on a parameter-report filename and was corrected; no numerical source was altered. One layout QA check rejected uppercase `Simultaneous` against a lowercase predicate and was corrected; saved mean and interval never changed. Initial Matplotlib cache-path warning was resolved with a Windows extended path. These were extraction/rendering issues, not failed science or excluded physical cases.

The pre-existing missing external manuscript and byte-identical backup are recorded in preservation QA; neither was restored, edited or designated authoritative. Current 950 protected scientific-file hashes, 862 staged items, original index/HEAD/status and evidence-source checkouts are compared before/after. No formal strategy, Stage 7 output, manuscript or official S05 is promoted or changed.

## Review Decision

**Scientifically consistent and visually review-ready**, subject to author acceptance of the retained legacy method and disclosures. Keep current official S05 unchanged until reviewed. Zero new optimizer searches, physical draws, production evaluations and bootstrap resamples.
