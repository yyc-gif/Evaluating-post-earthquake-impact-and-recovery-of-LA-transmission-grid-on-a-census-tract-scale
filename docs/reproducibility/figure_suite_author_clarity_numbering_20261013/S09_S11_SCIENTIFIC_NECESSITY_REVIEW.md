# Review using the former numbering

This memo uses **former S09/S11** to address the author's questions. They are
current **S08/S10** after continuous renumbering. No class, K or scientific result
is changed. Their artwork is retained while content reduction is considered.

## Former S09 C: robustness, not external validation

Its scientific question is whether memberships change with initialization,
geographic omission or policy-set omission. That question is relevant because
the fitting variables include policy-conditioned outcomes and a zero-heavy
initial-state coordinate. It does not prove that the selected K is physically
correct, causally meaningful or a universal community taxonomy. Four coarse
geographic leave-out cases are not independent geographic validation.

Stability analysis is an established diagnostic, but it is not automatically a
valid K-selection criterion or validation of clustering quality. See the primary
methodological discussion by von Luxburg, *Clustering Stability: An Overview*
(2010): https://arxiv.org/abs/1007.1075; and von Luxburg, Williamson and Guyon,
*Clustering: Science or Art?* (2012):
https://proceedings.mlr.press/v27/luxburg12a.html.

**Recommendation:** retain the robustness numbers as a concise table or compact
summary. A large separate C panel is not mandatory. Do not describe seed ARI=1
as evidence that the model is scientifically correct. Disclose the material
policy/geographic membership sensitivity instead of presenting a success badge.

## Former S09 D: within-fit ambiguity, not independent support

The per-class silhouette uses the same fitted input distances as the mean
silhouette curve. It is internal geometry, not an independent validation set.
Per-class silhouette is a recognized way to see ambiguous classes; see the
official example:
https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html.

Here it is not reassuring evidence: C2 mean silhouette is 0.01624, median
0.01538, and 44.21% of its tracts have negative silhouette. C3 has 12.20%
negative values; C1 has none. These are frozen values in
`figure_suite_ncv14_h2_k3_d3_20261013/K3_PER_CLASS_SILHOUETTE.csv`.

**Recommendation:** D need not occupy a large publication panel. Put its three
class summaries in a small table and explicitly describe C2 boundary ambiguity.
Keep the K-range inertia and mean silhouette as the figure's principal evidence.
Do not rerun fits or alter K to remove the inconvenient ambiguity.

## Former S11 versus Main Figure 6

Both use the same resource experiments, with 2pc50 fixed. Former S11 is not a
new hazard experiment. It displays absolute policy service-loss means across
crew or repair-duration conditions. Figure 6 displays Vulnerability-first minus
each of three policy references under those same conditions.

These are mathematically related summaries of the same simulations, not
independent validation. The archived `S11_Fig4_NUMERICAL_IDENTITY.csv` and
existing source/effect records document the shared reference values.

There can be two different questions:

- Figure 6: does the equity-priority trade-off change when resources change?
- Former S11: how large is the absolute recovery burden at each resource level,
  and do policy outcomes converge when resources are abundant?

The present eight-panel/ six-policy display repeats all four outcome families
and is visually dense. More policies alone do not constitute a new scientific
story. It should not be retained merely because those arrays exist.

**Recommendation:** retain absolute-resource outcomes only if they are used to
tell the second story explicitly. Use the same restrained mean-point visual
language as Figure 6. If that story is not needed in the paper, retain the full
policy/resource numerical table instead of another large figure. Do not use the
absolute outcomes and their differences as two independent confirmations.

The current revision changes neither this artwork nor its saved uncertainty
ranges. Deletion, mean-only reduction or a reduced panel set would be a separate
content decision; no such choice is silently made here.

## Figure 7 boundary

Figure 7 remains byte-identical to the approved Candidate A suite. The author
will give a new instruction for high-vulnerability AND slow-recovery hotspots.
This round does not define their threshold, calculate a score or reassign tracts.
