# Independent source-only control

This implements the author's previously requested missing control, rather than
searching again for an archived source-only case or renaming G0.

The baseline is `e = f F C`, with `F = 1[f >= 0.50]` and `C` denoting a path to
a retained Core source. The control is `e_off = f F`: only C is relaxed. Repair
times, orders, functionality states and tract dependency weights stay fixed.

The frozen accounting is:

`1 - f F C = (1 - f) + f (1 - F) + f F (1 - C)`.

Therefore its exact event-integrated source-only counterpart is:

`B_off = B_reference - L_source = integral[(1 - f) + f (1 - F)]`.

Linearity through the unchanged tract weights and population normalization
allows the control to be calculated from saved station integrals without
generating another trajectory. Both station-population sums and independently
mapped tract-population sums are verified for all 1,000 realizations per policy.

All comparisons use 2pc50, C57_D1, M1_UTILITY_003, threshold 0.50 and 480 hours.
All 2,315 tracts remain in the service accounting; represented population is
9,066,522. The three policies have the same 1,000 physical-sample hashes and
station order. The newly derived control is called `G4_SOURCE_OFF_050` in this
package only; the formal gate registry is not modified.

| Policy | Mean control-minus-reference service-loss gap (h) |
|---|---:|
| Impact-first | -4.167720433352381 |
| Hospital-first | -4.065130486843792 |
| Degree-first | -2.418438078384416 |

G0 removes F and C simultaneously and is not this control. The existing 0.05
and 0.75 threshold comparisons keep C active and are preserved separately.
Here "fixed source connectivity" means the requirement and source set are fixed,
not that every C(t) value is identical: changing the functionality cutoff can
also change the induced functional graph and its source-connected paths.
The source-only result is a diagnostic relaxation, not an alternative physical
delivery model or a rescheduled intervention.

Original external archive identities are in `SOURCE_ONLY_INPUT_AUTHORITY.json`.
The compact, hash-verified source inputs are retained for portable reproduction;
no external archive is needed to recalculate this package's control. The full
original archive remains local/manifest-bound, and is neither edited nor added.
