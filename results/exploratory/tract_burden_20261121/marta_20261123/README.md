# Marta discussion package

Start with [the one-page brief](MARTA_BRIEF.pdf) or its [editable text](MARTA_BRIEF.md), then see the [candidate manuscript passages](MANUSCRIPT_CANDIDATES.md) and [contribution review](CONTRIBUTION_REVIEW.md). The single candidate [screening figure](screening_coverage.png) has its own [caption](CAPTION.md).

## Calculation

The [analysis script](checks.py) reuses the parent analysis's frozen commit and SHA-256 validation. It reads the full frozen P2 and policy tables, preserves GEOID and population, and rebuilds policy differences before comparing to the earlier derived tract table. It does not use that derived table as an analysis input. The [QA record](quantitative_qa.json) reports all input hashes, identity checks, the earlier table comparison, and independent reference values.

For baseline B and policy increments D_j = T_j - B, covariance(B, mean(D_j)) equals the mean of covariance(B, D_j), with the same weights in every term. Population weights normalize over the tract population represented. The covariance uses the domain moment, dividing by the sum of weights. Each omitted-policy correlation uses a newly calculated standard deviation for its four-policy mean. Cancellation fraction is one minus the absolute net covariance divided by the sum of the absolute weighted terms. This is an arithmetic summary, and a fraction such as 0.910 describes cancellation of gross absolute covariance contributions.

The top quarter uses ceil(N/4) slots for each list, with GEOID as tie breaker. It takes 579 tracts in the full cohort and 575 in the positive cohort. At the full-domain P75, exact rank selection and the original inclusive percentile rule agree for all measures. The tables flag any differences when a group is omitted. For each single priority, use total deficit for that priority as the matched total screen. A supplementary fixed five-priority total screen is also included. Residents omitted are the sum of the frozen populations of target tracts not present on the screen. Geographic sensitivity recomputes all rank lists within each retained sample. Leave-outs include 47 10 km blocks in both cohorts and 10 broad regions in the positive-population cohort.

| Table | Row contents |
| --- | --- |
| covariance_by_policy.csv | Cohort, weighting and single policy covariance, both standard deviations and contribution to the mean |
| covariance_leave_one_policy_out.csv | Full mean and each omitted-policy mean, recomputed association and covariance balance |
| screening_coverage.csv | Cohort, target and screen at P70, P75 and P80, including cutoff and tie fields |
| screening_leave_block_out.csv | P75 coverage after each block or region omission |
| screening_spatial_summary.csv | Paired gain or loss in tract coverage and resident omissions across leave-outs |

## Rebuild

Use the dependencies in the parent [requirements.txt](../requirements.txt) for checks.py. Use Python 3.11 or newer and Git LFS. From the repository root:

~~~powershell
$cache = Join-Path $env:TEMP 'la_tract_burden_lfs'
python results/exploratory/tract_burden_20261121/marta_20261123/checks.py --cache $cache --fetch
~~~

Omit --fetch to reuse the verified files in an existing cache. For the original short-path local checkout, the default is its own .git/frozen_source_lfs directory. Use --output to regenerate the tables and figure elsewhere. To rebuild the one-page brief from its editable text, run render_brief.py with ReportLab installed.
