# One-Realization Service-Layer Integration Report

## Decision

**PASS — ONE-REALIZATION SERVICE-LAYER INTEGRATION VERIFIED**

The frozen Round 21 one-realization R1 trajectory was passed offline through the frozen Round 16 exporter and the frozen Round 14 Architecture B production interface. No source gate, recovery function, damage calculation, repair calculation, topology operation, scheduling operation, or new realization was executed in this round.

This is an interface-integration result only. It is not a recovery result and is not suitable for scientific interpretation.

## Frozen inputs

| Object | Frozen identity / SHA-256 | Check |
|---|---|---|
| Round 21 evidence NPZ | `5cfcd01fc2aa5853833a3083acee3b4b466c7974f8bfd9df3b5a7e06611b046e` | matched |
| Round 21 input manifest | `d7a99586bab333139008469f135b297a95334a288191966572dec6d55782111a` | matched |
| Main model / producer code | `90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145` | matched before and after |
| Round 16 exporter | `79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b` | unchanged |
| Round 14 production interface | `d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514` | unchanged |
| Service-node file | file SHA `ccf9e08b40a0df1326e7eb9f62addd92d9fa348f65a43dd4afc6a743845f2080`; canonical service-ID SHA `1c2533ea1ba4efd7894910e49c322654c90ec0eca6047908249a4c6e1b5d2f46` | matched |
| Attachment ledger | `b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e` | unchanged |
| W1 | `a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221` | unchanged |
| Tract metadata | `4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b` | unchanged |
| Canonical tract/population | `e2af72b613cec85e35834aca4785b782c433d981b4969fd87c761cccb7b529e8` | matched |

The Round 22 input manifest was written before production evaluation. Its SHA-256 is `0b46e8cd7c90fd863be7564f0a713aac6783c3af30928f525241d2f70e12ea0d`.

## Execution boundary

- `R1_SCIENTIFIC_EXECUTIONS = 0`.
- The Round 21 evidence NPZ was the only upstream state source.
- The production entry point `evaluate_service_layer_trajectory(...)` was called exactly once.
- The exporter was called offline; the Round 17 main-model export hook was not connected.
- No service or tract output was fed back to the R1 model.
- No T50, T80, T90, AUC, cumulative deficit, outage duration, recovery duration, SVI, hospital, or community-group analysis was computed.

## Exporter and production-loader parity

The Round 16 exporter produced exactly 2,480 long-form rows: 8 source times × 310 R1 stations. The trajectory retained source times `0, 1, 3, 6, 12, 24, 48, 72` and unit `hours_since_event`.

| Check | Compared | Mismatches | Maximum difference |
|---|---:|---:|---:|
| identified mask | 2,480 | 0 | 0 |
| identified numeric states | 2,448 | 0 | 0 |
| semantic missing states | 32 | 0 | 0 |

The four station-static missing IDs remained missing at all eight times: `301479`, `303265`, `304137`, and `305021`. IDs `306980` and `309598` remained identified; a numeric zero for either is therefore an identified zero rather than missing.

The exported canonical trajectory SHA-256 is `7cde8dcf291591b7248edd0ca7391ab389db6920326d566adbdd6652b352fb3e`.

## Independent service-state oracle

The oracle was implemented separately from the production propagation helper. For Class A and Class B it performed one direct lookup of the selected upstream R1 semantic state. Class C was set to semantic missing. It did not apply a source gate, second damage multiplier, carry-forward, nearest fill, or service-node damage.

| Check | Compared | Mismatches | Maximum difference |
|---|---:|---:|---:|
| complete A/B/C missing pattern | 1,568 | 0 | 0 |
| Class A/B numeric states | 1,472 | 0 | 0 |
| Class C semantic missing cells | 96 | 0 | 0 |

The production and oracle service arrays have the same SHA-256: `8d08239b9b76691260bffa3781dafc54f5026f8e49c3ac59984a6e2c16f6d5ed`.

Dynamic service variation was exercised by the frozen Round 21 trajectory: 4 A/B service nodes changed over the eight time points, comprising 2 Class A nodes and 2 Class B nodes. Of the four Round 21 mechanically selected test-damaged R1 IDs, `300008` and `300105` were A/B upstream targets. These counts are QA evidence only.

## Independent tract oracle

The tract oracle was implemented directly from the original frozen W1 array and the independent service-state oracle. It did not call either production propagation helper. It computed resolved mass, unresolved mass, known available mass, lower bound, upper bound, width, and the conditional-resolved diagnostic without reweighting W1.

All 6,536 tract-time rows matched the production output for every field:

| Field | Compared rows | Mismatches | Maximum absolute difference |
|---|---:|---:|---:|
| resolved mass | 6,536 | 0 | 0 |
| unresolved mass | 6,536 | 0 | 0 |
| known available mass | 6,536 | 0 | 0 |
| lower | 6,536 | 0 | 0 |
| upper | 6,536 | 0 | 0 |
| width | 6,536 | 0 | 0 |
| conditional-resolved diagnostic | 6,536 | 0 | 0, with NaN semantics matched |

The production and oracle tract-core arrays have the same SHA-256: `76a6a06a956ea47990451f53f21e8beda11f633c3ab741401447a50fc105a8a5`.

Resolved plus unresolved mass differed from 1 by at most `1.999955756559757e-12`, within the frozen W1 serialization tolerance of `5e-12`. Production unresolved mass matched the original W1 mass on Class C for every tract and time, with maximum difference 0. This proves that missing candidate mass was not redistributed or renormalized.

Tract interval width was time-invariant within the required `1e-12` tolerance. The largest floating-point deviation from the first-time width was `1.1102230246251565e-16`.

## Aggregate parity QA

The eight population-weighted aggregate rows were retained only for parity checking. Production and independent-oracle lower, upper, and width values matched in all 24 compared cells with maximum absolute difference 0. The actual aggregate values are deliberately not reported.

The production and oracle aggregate arrays have the same SHA-256: `1c2c2401286b8da4d19c9827634648990a9381e88ddc4ba28af7f690ccbb48e7`.

## Deliverable identities

| File | SHA-256 |
|---|---|
| `ONE_REALIZATION_SERVICE_LAYER_INPUT_MANIFEST.json` | `0b46e8cd7c90fd863be7564f0a713aac6783c3af30928f525241d2f70e12ea0d` |
| `ONE_REALIZATION_SERVICE_LAYER_PARITY_QA.csv` | `327e8d83e1fd8b065601bf934ba501fd5d43c74810d693f984383c4e79a2c9e9` |
| `ONE_REALIZATION_SERVICE_LAYER_EVIDENCE.npz` | `bd29e2a761f53d1b935d37adc355530d16beed5725d56554a7e74017e1ee53e5` |

## Direct answers

1. **Was any source gate or recovery executed in this round?** No. `R1_SCIENTIFIC_EXECUTIONS = 0`.
2. **Did all 2,480 Round 21 upstream cells enter the production loader without semantic loss?** Yes. The complete mask matched, all 2,448 identified numeric cells matched, and all 32 missing cells remained semantic NA.
3. **Did all 1,568 service cells match the A/B/C oracle?** Yes.
4. **Did all 1,472 A/B cells equal their selected upstream R1 state?** Yes, with zero mismatches and no repeated multiplication.
5. **Did all 96 Class C cells remain missing?** Yes.
6. **Did all 6,536 tract-time rows match the independent W1 oracle?** Yes for all seven checked fields.
7. **Was W1 ever renormalized because of missing state?** No. Unresolved mass equals the original Class C W1 mass at every time.
8. **Was tract interval width time-invariant?** Yes within `1e-12`; maximum deviation was `1.1102230246251565e-16`.
9. **Were the eight aggregate rows used only for parity QA, and did they all match?** Yes. All 8 rows × 3 fields matched, and their values are not reported as results.
10. **Did the Round 21 trajectory exercise dynamic service variation?** Yes. Four A/B service nodes changed: two Class A and two Class B.
11. **Was any paper recovery KPI computed?** No.
12. **Did all frozen code and input hashes remain unchanged?** Yes.
13. **Is the Architecture B real scientific-to-service integration loop closed?** Yes, for the authorized one-realization offline integration boundary: frozen R1 scientific trajectory → frozen exporter → frozen production loader → A/B/C service states → W1 tract intervals.
14. **What is the next step?** Return to **R1-310 scheduling input readiness**. Do not begin 32×4. Freeze and QA the 310-node task set and task eligibility, repair-duration scenario, road/travel readiness including unresolved access flags, rule-based strategy inputs, Architecture B population/hospital/SVI priority inputs, GA sequence dimensional readiness, and the 29/114-crew scenario definitions before authorizing a new pilot.

