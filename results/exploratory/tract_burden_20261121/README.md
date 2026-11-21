# Reproduce the tract burden analysis

This directory accompanies the independent study note. It is based on committed frozen results at 1887bca4872f24d6d547637440db5619a4423452. The default remote is origin in the LA grid repository. All analytical inputs are immutable Git LFS objects. The script checks byte counts and SHA-256 before opening an input, checks the three hashes recorded in the exploration packet, verifies one-to-one 11-digit GEOID joins, and writes only to the destination and fetch cache. Neither the supplied exploratory ZIP nor the manuscript is needed for the computational rebuild.

From a checkout of the review branch with Git LFS and Python 3.11 or newer:

~~~powershell
python -m pip install -r results/exploratory/tract_burden_20261121/requirements.txt
$tractCache = Join-Path $env:TEMP 'la_tract_burden_lfs'
python results/exploratory/tract_burden_20261121/analyze.py --fetch --cache $tractCache
~~~

Reuse the same cache without --fetch for an offline rebuild. Use --repo to point to a different checkout of the same repository and --output to write to a different directory. Git must have the frozen commit named above. With Windows paths, keep the checkout and the cache paths short.

## Tables and interpretation

| File | Row and contents |
|---|---|
| source_qa.json | Git source revision, paths, SHA-256, byte counts, row/missing counts, and decimal and floating point checks |
| tract_metrics.csv | One row per frozen GEOID. Read tract_id as string to preserve the initial zero. Population and SOVI membership are frozen. Blank type or positive-cohort screen fields are expected for zero-population tracts. broad_region is archived only for the positive cohort. |
| associations.csv | One row per added-deficit definition and cohort, with unweighted and population-weighted linear and rank association |
| group_distributions.csv | Group × deficit field × cohort. Equal-tract quantiles are interpolated. Population quantiles are inverse empirical CDF values. Counts of negative policy-minus-baseline differences are retained. |
| signed_vulnerability_gaps.csv | Q4 minus Q1, keeping the sign for both means and medians |
| top_quartile_overlap.csv | Thresholds, ties, tract and resident counts/shares, and Jaccard. In ensemble_added_vs_policy_added rows, the baseline field is the five-policy added deficit and the added field identifies the comparison. |
| overlap_by_vulnerability.csv | Frozen vulnerability quartile within each P75 burden group |
| spatial_overlap_by_block.csv | Each block's total count and population and its four joint burden categories. The blank broad region row contains only the 16 zero-population tracts. |
| spatial_leave_block_out.csv | Omit one spatial group, then recompute correlations, Q4−Q1 and per-burden P75 screens. Report ranges as geographic sensitivity, without a sampling CI. |
| overlap_feature_profiles.csv | Matched network-feature distributions by joint burden category |
| spatial_predictive_diagnostics.csv | Pooled predictions from leave-one-block-out logistic models. Target and baseline rank flags use their cohort-specific fixed P75 cutoffs. Standardization and fitting use training blocks only. Brier scores are shown per tract and population weighted. Models are exploratory. |

Five main comparisons use Impact-first, Hospital-first, Degree-first, Betweenness-first, and Vulnerability-first. The arithmetic removal of the source-path contribution uses the same four policies as MeanDelta_no_vulnerability because the dedicated formal component table lacks Vulnerability-first. This subtraction reranks existing mean quantities. See the report for its scope and interpretation.
