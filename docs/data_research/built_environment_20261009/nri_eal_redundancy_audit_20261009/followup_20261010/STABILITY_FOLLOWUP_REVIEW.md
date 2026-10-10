# Independent follow-up: B versus D K-means initialization stability (2026-10-10)

This is an exploratory numerical study using the frozen source records from commit 65f388f9710566ffa845808bd7b10503de4da608. Its source input hashes appear in results/SUMMARY.json. The original manuscript, Stage 7 and the author's audit branch remain unchanged.

**Motivation.** The parent audit compared five random seeds with n_init=10 and found B to have poor seed agreement at fixed k=5 (median pairwise ARI 0.604). That does not distinguish genuine label non-identifiability from insufficient initialization search. We tested 20 seeds (42–61), increasing the KMeans restarts while holding fixed the 2,291 GEOIDs, exactly the same T80, Init_Supply, social score, four grid variables, population density, housing age, domain budget, model variables and preprocessing.

## Original Stage7 domain weights; log exposures; fixed k=5

| Model | n_init | Median pairwise ARI | Minimum pairwise ARI | Worst objective gap (%) |
|---|---:|---:|---:|---:|
| B | 10 | 0.68535 | 0.27267 | 2.65300 |
| B | 50 | **1.00000** | **0.99284** | 0.000286 |
| B | 150 | **1.00000** | **0.99857** | 0.0000195 |
| D | 10 | 0.95519 | 0.49871 | 0.32327 |
| D | 50 | 0.97057 | 0.95075 | 0.003271 |
| D | 150 | 0.98342 | 0.96024 | 0.001186 |

KMeans initialization explains **most** of B's original five-seed problem. The high-restart outputs are near optimal within the experiments, but cannot prove a global optimum. B must not be discarded solely on the original five-seed ARI.

## Equal weight per domain: 20 seeds, k=4 or k=5

| k | Model | n_init | Median pairwise ARI | Minimum pairwise ARI |
|---:|---|---:|---:|---:|
| 4 | B | 10 | 0.92832 | 0.53988 |
| 4 | B | 100 | **0.99578** | 0.90746 |
| 4 | D | 10 | 0.88052 | 0.24977 |
| 4 | D | 100 | **0.97636** | 0.88185 |
| 5 | B | 10 | 0.95079 | 0.47969 |
| 5 | B | 100 | **0.96630** | 0.93410 |
| 5 | D | 10 | 0.98235 | 0.92150 |
| 5 | D | 100 | **0.99038** | 0.97993 |

The residual alternative assignments at equal-domain k4/k5 deserve reporting. Improved optimization does not validate arbitrary k, weights or new urban-form input data.

## Scientific implications

After high-restart optimization, B-versus-D pairwise ARI remains around **0.301** in the original-weight k5 setting and around **0.514** (equal-weight k4) or **0.499** (equal-weight k5). The two scientific variable choices still produce substantively different partitions; the contrast is NOT a random-seed artifact.

B: mandatory SOVI_SCORE plus EAL_SCORE, combining total relative multi-hazard monetary expected loss and economic exposure in one score. B cannot separately report building-stock magnitude.

D: mandatory SOVI_SCORE, log1p(NRI_BUILDVALUE) and ALR_NPCTL, distinguishing economic building stock and exposure-normalized multi-hazard loss-rate percentile. D is scientifically preferable ONLY when those are intended as distinct dimensions; the evidence no longer supports preferring D because it seemed algorithmically stable under n_init=10.

All natural hazards in the FEMA source remain included. The 98.1563% earthquake share of local total EAL is a verified property of this source/study geography, not an analyst earthquake-only filter. Neither D nor B is pure physical hazard or balanced hazard-type diversity. SOVI remains mandatory.

Final Stage7 input choice stays conditional on B-versus-T80 recovery definition, newly verified physical built-environment variables, domain weighting and uncertainty. No original scientific data or figures were changed.

## Output and verification

Implementation: test_initialization_stability.py and test_equal_domain_stability.py. Result files: results/SUMMARY.json, results/INITIALIZATION_SUMMARY.csv, results/EQUAL_DOMAINS_SUMMARY.json, results/B_VS_D_ARI.csv, results/EQUAL_DOMAINS_B_D_ARI.csv, results/BEST_LABELS.csv. GitHub Actions run 38033589354 completed successfully with pinned scikit-learn 1.5.1 and independent LFS input hydration. These are exploratory new labels, NOT approved final Stage7 clusters.
