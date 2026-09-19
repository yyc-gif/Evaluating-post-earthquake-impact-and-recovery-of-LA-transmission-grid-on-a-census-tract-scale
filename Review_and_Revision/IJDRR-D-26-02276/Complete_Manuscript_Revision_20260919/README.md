# Complete Position B manuscript revision

Scientific result basis: **87110dad035ddb6eb694235330cd2547d9ba5588**.

This package rewrites the complete paper as a conditional restoration-decision study with two targeted assumption contrasts. It preserves the original manuscript, original result files, and candidate history. It does not perform new GA searches, physical sampling, scheduling, source gating, or service propagation.

## Editable documents

- `REVISED_MANUSCRIPT.docx`: complete clean article, including title, abstract, introduction, methods, results, discussion, conclusion, declarations, references, four main figures, and Tables 1–3 (Table 2 has two parts).
- `SUPPLEMENTARY_MATERIAL.docx`: five supplementary sections, Tables S1–S5 (S3 has two parts), and Figures S1–S2.
- `RESPONSE_TO_REVIEWERS.docx`: editorial response, both overall assessments, all seven Reviewer 1 comments and all sixteen Reviewer 2 comments. Original comment wording is quoted; response locations use stable manuscript section/table/figure labels.
- `CLAIM_EVIDENCE_CROSSWALK.docx`: one-page original/superseded claim → revised claim → evidence table.

The matching Markdown files contain the same resolved content for review and version comparison. DOCX text, tables, and equations are editable. Figures are embedded and also supplied separately as PNG and vector PDF in `Figures/`. Original funding and competing-interest statements are retained; the AI-assistance declaration is expanded to describe the actual assistance rather than language polishing alone. No author contribution roles have been invented from the original blinded statement. As with any draft, the authors retain responsibility for the final submission and declarations.

## Scientific evidence used

All quantitative tables and plots are drawn from the retained `Targeted_Methodological_Strengthening_20260919` directory. Search curves alone use the historical `26_GA_Reproducibility_and_Revised_Paired_Pilot_20260919/GA_CONVERGENCE_BY_SEED.csv`.

| Manuscript evidence | Retained source |
|---|---|
| Baseline means, denominator comparison, Q1–Q4, gap/Gini, DS4 levels | `METRIC_DISTRIBUTIONS.csv` |
| Strategy effects, uncertainty intervals, changes under DS4×2 | `PAIRED_EFFECTS.csv` |
| Mean-effect versus realization-first population classes | `WINNER_LOSER_POPULATION.csv` |
| Direct/attached/partly unresolved evidence strata | `GROUP_ABSOLUTE_BURDEN.csv` |
| Metric-specific lowest-value frequencies | `METRIC_RANK_FREQUENCIES.csv` |
| Same-objective candidate scoring and provenance | `CANDIDATE_OBJECTIVE_COMPARISON.csv`, `FROZEN_CANDIDATE_SEQUENCES.csv` |
| Model interpretation and interface accounting | `TARGETED_METHODOLOGICAL_STRENGTHENING_RESULTS.md` and its saved evidence |
| Original reviewer wording | `01_Reviewer_and_Decision/IJDRR-D-26-02276_editor_review_transfer_record.md` |

`Supplementary_tables/` contains byte-for-byte copies of the retained metric distributions, paired effects, and ranking frequencies. In these files, historical strategy labels `GA-Balanced` and `GA-HospFirst` mean the corrected deterministic initializers in the final comparison; they do not assert GA optimality. Conditions are `corrected_baseline`, `AB_lambda_0.5`, `AB_lambda_2`, and `DS4x2`. The `candidate_correction_minus_R26` contrast is historical provenance, not an additional physical experiment. Unavailable temporal metrics in offline A/B conditions remain missing.

## Rebuilding the documents only

`build_figures.py` reads saved CSV statistics and produces the six figure pairs. `build_documents.py` combines the text in `source/*.md.in`, the figures, and retained summary values into DOCX and complete Markdown. Neither script imports or calls a scientific execution driver. Use a Python environment with matplotlib/pandas/numpy for figures and python-docx/pandas for documents.

The DOCX package was rendered through Microsoft Word for page inspection; the figures retain vector PDF versions. Rendering files are temporary and are not additional scientific outputs. The formulas remain native Word equations, not equation screenshots.

## Claims deliberately not made

No actual delivered-power or feeder validation; no equity-optimal plan or Pareto frontier; no global GA optima; no cross-objective fitness comparisons; no new independent evaluation sample; no equivalence claim from small or zero-crossing differences. Twelve fully unresolved tracts remain outside numeric burden summaries and separate from near-zero effects. The ±1 h classification threshold is practical, not statistical significance.
