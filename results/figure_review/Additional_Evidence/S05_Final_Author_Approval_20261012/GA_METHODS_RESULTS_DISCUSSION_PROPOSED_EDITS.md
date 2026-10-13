# Copy-ready GA amendments for author review

These edits use only frozen archived evidence. No edits have been applied to a manuscript, official caption, numbered figure or scientific output. Full-DOCX paragraph locations below are **provisional** because the previously confirmed working file is missing; the inspected backup is not designated current. The current revision-branch caption and meeting-summary locations are definitive at `c0a11ffb4df523111efe6c8e65cfe86eadffec3c`.

## Methods: final GA execution

Replacement for the GA-specific Methods paragraph (backup p21, section 2.4; meeting summary p50):

> Restoration priority was represented as a full permutation of the 92 substations and evaluated using the unchanged population-dependency-weighted normalized cumulative service-loss objective on 64 fixed 2pc50 planning realizations. Fitness was the negative mean loss. Each of 20 independent GA runs began with 100 independently generated uniformly random permutations. Population size remained 100; ordered crossover probability was 0.80, swap-mutation probability 0.10 and tournament size 3. One previous-generation elite was retained using the validated legacy implementation, which replaces the last generated offspring before its evaluation. A separate, initially empty passive archive retained the best chromosome actually evaluated. No fixed-rule order, heuristic warm start or inherited optimized chromosome was inserted; adaptive mutation, restarts and diversity replacement were disabled. Run-local exact-permutation caches avoided duplicate expensive evaluations, and each run stopped at 100,000 distinct evaluated permutations rather than a fixed generation count. The final sequence was the minimum-loss archived final-budget result among seeds 2026103100-2026103119; losses within 1e-9 h of the minimum were resolved by the lowest seed. This archived rule selected seed 2026103108. Physical-validation outcomes were not used to reselect the sequence.

Keep the existing physical sampler, scheduler, source gate, population mapping and loss definitions where already described. Do not duplicate their equations or add a surrogate objective. This paragraph describes the actual legacy method, not the later post-evaluation worst-offspring implementation.

## Supplementary Methods: reproducibility and scope

Place after the final execution paragraph or in the supplementary search protocol:

> The selected 92-station permutation has SHA-256 edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a (newline-separated station IDs with a final newline). Its archived planning loss is 32.99552241352315 h. Exact initial pools, random-state receipts, strict best-observed histories and final-budget records are retained for all 20 seeds. Tournament fitness ties retain the first sampled contender; preceding-generation elite ties use the lexicographically smallest station-ID tuple; exact passive-archive ties retain the first observed chromosome. These tie rules and legacy last-position elitism are part of the retained execution identity, not a claim that legacy replacement is the best engineering design. Pure-random initialization was adopted as a post-data methodological judgment, rather than under a successful automatic admission rule. Only 10 of the 20 final-budget runs met the earlier strict proximity cutoff of 32.99884077388271 h, below the registered 90% single-run criterion. Multi-run finite-budget selection is therefore reproducible, but guaranteed near-optimal single-run performance is not established.

> The archived planning horizon was 2855.2540131100995 h. Existing order-independent completion-bound evidence, with a maximum of 134.33255016512265 h across the 64 planning states and full source-connected recovery, establishes numerical equivalence to the 480-h planning integral. This equivalence is retained rather than retrospectively changing the planning objective. The candidate's already completed independent production check agreed with the compiled planning evaluator within a maximum per-case absolute difference of 3.439026841078885e-12 h.

Add a separate validation paragraph after original formal-evaluation accounting (backup p25, section 2.6):

> After freezing the sequence and analysis plan, the candidate was evaluated on a fresh cohort of 2,000 physical realizations under 2pc50, C57_D1, the unchanged 92-station/318-edge network, Core-source service gate and 0.5 functionality threshold. Policies shared each complete physical draw. The primary contrast was GA minus Impact-first in population-weighted normalized cumulative service-loss hours over 0-480 h; negative values favor GA. The original analysis resampled complete paired physical realizations 20,000 times and used the prespecified Bonferroni simultaneous intervals for its two population-loss contrasts. The interval in Figure S05 retains that original family and is not recomputed for the figure. Optimizer seeds and physical realizations are distinct replication units. The separate later revised-elitism validation cohort does not contribute to this analysis.

## Results: search and independent validation

Replace only the outdated GA-specific statements in backup p43 (Results 3.5) or insert a dedicated subsection after the fixed-rule results:

> The random-only GA performed genuine search from its scored initial populations: initial best losses ranged from 35.238959 to 36.865575 h and final best losses from 32.995522 to 33.003661 h across the 20 fixed-budget runs (Figure S05A,B). The archived selection rule chose seed 2026103108, with planning loss 32.99552241352315 h. Final outcomes were close, but only 10/20 satisfied the previously registered strict proximity cutoff; the 90% single-run reliability criterion was not met. These are finite-budget outcomes, not a certificate of global optimality.

> In the candidate-specific fresh 2,000-realization validation, the mean paired GA-minus-Impact-first population loss difference was -0.532675 h (simultaneous 95% confidence interval -0.563982 to -0.502321 h). Outcomes improved in 1741 realizations (87.05%) and worsened in 259 (12.95%), with no ties. Figure S05C preserves both tails of the empirical distribution rather than describing the mean as universal benefit. Mean component differences were +0.277475 h for self loss, +0.010638 h for threshold loss and -0.820788 h for source-path loss, yielding the -0.532675 h net difference (Figure S05D). Thus source-path loss reduction outweighed increases in the other components. The mean per-realization absolute SOVI Q4-Q1 burden gap increased by 0.232733 h and population-weighted tract burden Gini increased by 0.009790. Average population efficiency and distributional equality did not improve together.

Retain original non-GA results with their original 1,000-case denominators. Do not convert any Impact-first curve to a GA curve or use this fresh-cohort mean to alter existing policy bars. The proposed S05 does not establish a T80 or hospital-associated effect by itself; those distinct metrics must be quoted only from the same candidate's saved endpoint records when needed.

## Discussion: meaning and limitations

Insert adjacent to optimization/model boundaries (backup p47); do not rewrite unrelated community or network discussion:

> The independent result supports a lower mean modeled population service-loss burden for this frozen random-initialization GA sequence relative to Impact-first under the fixed 2pc50/C57_D1 experiment. It does not establish global optimality, optimizer-wide superiority, guaranteed single-run convergence or improved fairness. Pure-random initialization remains a post-data methodological choice, and failure of the earlier 90% single-run proximity criterion should not be obscured by the close final losses. The adverse absolute-quartile-gap and Gini changes demonstrate that a population-mean objective is not an equity objective. Source-path reduction is an event-integrated accounting contribution within the model, not an identified causal effect of moving a particular station. Connectivity-based service availability does not measure delivered MW, verified power flow, actual customer restoration or hospital operating continuity. These conclusions remain conditional on the fixed hazard, damage and repair scenarios, crew/travel model, source proxy and tract dependency mapping.

## Minimal abstract and conclusion replacements

Replace only the obsolete GA sentence in the backup Abstract p4:

> A separately frozen pure-random GA sequence reduced mean population service loss by 0.533 h relative to Impact-first on 2,000 fresh physical realizations, while increasing the absolute vulnerability-quartile burden gap and tract Gini.

Replace only the obsolete incumbent-retention sentence in backup Conclusions p49:

> Independent validation of the frozen pure-random GA sequence supports lower mean modeled population burden than Impact-first, but not universal realization-level benefit or improved distributional equality.

## Caption cross-reference replacements

Use `S05_CONCISE_MANUSCRIPT_CAPTION.md` for S05. Keep identifier S05; no downstream figure renumbering is required. Proposed edits to the final sentence of Figure 4 and affected clauses of S11-S13 are given in audit C09-C12. State explicitly that those figures show the original fixed-rule ensemble and S05 the separate candidate-specific cohort. Do not add the final GA to four-hazard or resource-comparison legends without corresponding evidence and separate author approval.

## History and bibliography

Historical deterministic-incumbent/inversion/generation-budget studies remain in their original diagnostic and provenance packages, not the final execution description. Explain the difference only in the supplementary provenance needed to prevent misattribution; the main method need not narrate every exploratory algorithm. No new author-year citation or DOI is introduced. Existing model/source citations remain attached to unchanged model definitions; add repository execution-protocol, legacy-engine and validation-archive references to the reproducibility statement. The actual full manuscript's bibliography and paragraph locations remain a final editorial gate once its accessible current version is supplied.
