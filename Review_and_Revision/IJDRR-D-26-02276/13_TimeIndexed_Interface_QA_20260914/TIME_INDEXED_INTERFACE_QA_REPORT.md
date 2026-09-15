# Time-Indexed Service-Layer Interface QA Report

Date: 2026-09-14

Architecture: **B — two-layer service-access proxy**

Targets: CENTER 300232 and MESA 301541

Decision: **PASS — TIME-INDEXED INTERFACE VERIFIED**

## Scope

This round tested whether Architecture B can consume an explicit, external, multi-time R1 effective-state trajectory and propagate it to service states and tract availability intervals without residual state.

It did not call a source gate, connectivity routine, component computation, shortest path, node/edge removal, or topology propagation. It did not sample damage, PGA, fragility, repair, or travel; dispatch crews; schedule tasks; run GA/Monte Carlo; or calculate T50/T80/T90/AUC or any recovery metric.

`time_index` is a dimensionless QA index. It is not elapsed time, earthquake time, outage duration, or repair time. No interpolation was performed.

## Frozen-input integrity

The test required the exact 21-node source-scenario hash before any calculation:

`c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3`.

It also verified:

- R1 IDs: 310; ID hash `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5`.
- Service IDs: 196; ID hash `1c2533ea1ba4efd7894910e49c322654c90ec0eca6047908249a4c6e1b5d2f46`.
- Attachment ledger SHA-256: `b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e`.
- W1 SHA-256: `a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221`.
- Tract/population input SHA-256: `4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b`.
- T0 node baseline SHA-256: `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384`.
- T0 tract interval SHA-256: `e285c9bbc8a1ecb9dd7057060ef4f5453edea42f70ffb4b7d42d9c0975e3ed9a`.
- Frozen topology SHA-256: `e2dd039ec40336ea800adc29aa6cf790ae3d89553c1491c149096b3be6377090`.

All frozen hashes were identical before and after the test. Source membership, topology, service attachments, W1, Class C membership, and tract/population inputs were not modified.

## Explicit external trajectory and loader QA

`EXTERNAL_R1_EFFECTIVE_STATE_TRAJECTORY.csv` contains 1,550 rows: five time indices × 310 exact R1 IDs. Its SHA-256 is:

`b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6`.

| time_index | CENTER | MESA |
|---:|---:|---:|
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 2 | 0 | 0 |
| 3 | 1 | 0 |
| 4 | 1 | 1 |

All other R1 states retain T0 at every index. The loader checks exact ID membership, no duplicates or omissions, unique strictly increasing indices, finite numeric state values in `[0,1]`, the exact CENTER/MESA pattern, and exact non-target equality to T0.

The frozen T0 has four registration-unresolved network states represented semantically as `NA`. To meet the finite-file requirement without changing their meaning, the trajectory serializes each as `(effective_state_value=0, state_identified=False)`. The loader restores `NA` before consumption and verifies that the identified/missing mask never changes. No A/B service attachment targets those four records.

The trajectory file is an external interface input produced without model-state generation, source-gate calculation, or topology propagation.

## Attachment sets recalculated from frozen inputs

No node count was hard-coded.

### CENTER 300232

CENTER has seven service nodes: one Class A direct identity and six Class B named-system proxies.

| Service node | Class | Candidate relations | Population-weighted W1 mass |
|---|---|---:|---:|
| CENTER | A | 25 | 44,276.533333318 |
| DAELEY PT | B | 1 | 885.250000000 |
| DOWNEY | B | 12 | 18,347.266666655 |
| FLORADAY | B | 6 | 9,995.116666665 |
| PASSONS | B | 19 | 34,999.449999988 |
| RIVERA | B | 11 | 15,133.049999993 |
| RONNIE PT | B | 2 | 2,654.000000000 |

`C_POP = 126,290.666666619` population-weighted W1 units, or `0.03535422531477355` of strict-SCE population. CENTER affects 51 unique tracts.

### MESA 301541

MESA has 11 service nodes, all Class B. It has no direct-identity service node.

| Service node | Class | Candidate relations | Population-weighted W1 mass |
|---|---|---:|---:|
| AMALIA | B | 12 | 17,393.099999988 |
| BELVEDERE PT | B | 1 | 607.000000000 |
| BICKNELL | B | 8 | 9,595.749999995 |
| ELEMENTARY PT | B | 1 | 678.000000000 |
| GABRIELINO PT | B | 1 | 1,288.999999999 |
| GARVEY | B | 14 | 16,817.833333321 |
| IVAR | B | 8 | 11,922.266666662 |
| MESA | B | 18 | 29,448.599999987 |
| MICHILLINDA | B | 9 | 15,107.549999994 |
| TEMPLE | B | 7 | 9,832.433333328 |
| TERRACE | B | 5 | 7,011.583333327 |

`M_POP = 119,703.116666600` population-weighted W1 units, or `0.03351008486385798` of strict-SCE population. MESA affects 69 unique tracts.

The CENTER and MESA affected-tract sets have **zero overlap**. As specified, no third node was added. The superposition identity was still tested over every tract rather than treated as automatically true because the intersection is empty.

## Analytic expectation frozen before propagation

From W1 and the attachment ledger:

- `C_r` is the sum of a tract's W1 mass on the seven CENTER-attached nodes.
- `M_r` is the sum on the 11 MESA-attached nodes.
- `U_r` is the frozen Class C unresolved mass.
- `[L0_r,H0_r]` is the frozen T0 interval.

Expected intervals were calculated before service propagation:

| Index | Expected interval |
|---:|---|
| 0 | `[L0, H0]` |
| 1 | `[L0−C, H0−C]` |
| 2 | `[L0−C−M, H0−C−M]` |
| 3 | `[L0−M, H0−M]` |
| 4 | `[L0, H0]` |

At every index, expected interval width is `U_r`.

## Service-state propagation result

Each A/B service node performs one lookup of its named upstream R1 state at each index. Class C performs no lookup and remains `NA`.

- t0: all 184 A/B nodes reproduce baseline 1; all 12 C nodes are missing.
- t1: only the seven CENTER-attached nodes are 0.
- t2: those seven remain 0 and the 11 MESA-attached nodes become 0.
- t3: all seven CENTER nodes return to 1; all 11 MESA nodes remain 0.
- t4: CENTER and MESA nodes return to 1; Class C remains missing.

All 980 service-node/time records match the analytic state expectation within `1e-12`. No service node has two upstream attachments. Sharing one upstream state across multiple service nodes is a community-mapping relation, not repeated physical damage.

## Tract propagation and superposition

All 4,085 tract/time records satisfy:

- observed lower equals expected lower within `1e-12`;
- observed upper equals expected upper within `1e-12`;
- interval width equals the frozen Class C width within `1e-12`;
- interval width also matches T0 by exact floating-point equality in all 4,085 records.

At t2, all 817 tract changes satisfy:

`Lower_t2 − Lower_t0 = −(C_r + M_r)`.

This global identity tests algebraic superposition even though the two affected-tract sets do not overlap. The overlap-specific test is not applicable; it was not replaced by a third target.

The time-transition checks also pass:

- t2→t3 equals `+C_r` for every tract: only CENTER is restored.
- t3→t4 equals `+M_r` for every tract: only MESA is restored.
- t4 network, service, and tract vectors exactly equal t0, including semantic `NA` values.

There is no time shift, cumulative-delta error, forward fill, event-history residual, Class C conversion, or W1 renormalization.

## Population-weighted lower-bound QA series

This table is a dimensionless interface-QA sequence. It is not a recovery curve.

| time_index | CENTER | MESA | Expected lower | Observed lower | Observed upper | Width |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 1 | 0.959156949834623 | 0.959156949834627 | 0.999999999999710 | 0.040843050165083 |
| 1 | 0 | 1 | 0.923802724519850 | 0.923802724519854 | 0.964645774684936 | 0.040843050165083 |
| 2 | 0 | 0 | 0.890292639655992 | 0.890292639655996 | 0.931135689821078 | 0.040843050165083 |
| 3 | 1 | 0 | 0.925646864970765 | 0.925646864970769 | 0.966489915135852 | 0.040843050165083 |
| 4 | 1 | 1 | 0.959156949834623 | 0.959156949834627 | 0.999999999999710 | 0.040843050165083 |

The analytic/observed differences of about `4×10−15` result from floating-point summation order and are below the `1e-12` acceptance threshold. Aggregate lower and upper changes match the exact W1-derived `C_POP` and `M_POP` shares.

## Decision

**PASS — TIME-INDEXED INTERFACE VERIFIED.** Architecture B consumes the external five-index R1 effective-state trajectory, propagates multiple upstream states without duplicate damage/state operations, preserves unresolved Class C mass, respects linear superposition, and returns exactly to baseline with no state history.

This is an interface test. It supports no earthquake, failure, restoration, timing, customer-outage, strategy, or policy conclusion.

## Next allowed step

The next single allowed step is to **freeze the verified trajectory-loader, service propagator, tract-interval aggregator, and regression fixtures as the production interface contract** and run the same T0–T4 fixture as a regression test from the production module. That step may refactor tested interface code only; it must not generate upstream states, invoke source/topology functions, or introduce damage, repair, scheduling, optimization, or stochastic computation.

## Direct answers

1. **CENTER/MESA attachments:** CENTER 7 = 1 A + 6 B; MESA 11 = 0 A + 11 B.
2. **Exact masses:** `C_POP=126,290.666666619`; `M_POP=119,703.116666600` population-weighted W1 units.
3. **Affected tracts:** CENTER 51; MESA 69.
4. **Overlap:** 0 tracts; no third target was added.
5. **Service states:** all 980 service/time states match the expected t0–t4 pattern.
6. **t2 superposition:** all 817 tracts satisfy `−C_r−M_r`; overlap-specific evaluation is not applicable because the intersection is empty.
7. **Interval width:** unchanged in all 4,085 records, including exact equality.
8. **Aggregate bounds:** every index matches the analytic expression within `1e-12`.
9. **t3:** restores CENTER only; the tract transition equals `+C_r` while MESA remains unavailable.
10. **t4:** exactly restores network, service, and tract T0 states.
11. **Gate:** PASS — TIME-INDEXED INTERFACE VERIFIED.
12. **Next allowed work:** production-interface freeze and fixture regression only; all recovery and stochastic work remains prohibited.
