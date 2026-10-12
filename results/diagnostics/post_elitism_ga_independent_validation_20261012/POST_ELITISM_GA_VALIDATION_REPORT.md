# Post-evaluation GA prospective physical validation

Exactly 2,000 fresh physical realizations, shared across three frozen sequences: 6,000 native production evaluations and 6,000 independent compiled checks. Zero optimizer searches. Native source gate, Core-source proxy, 2pc50, C57_D1, 92 stations/318 edges, directed travel, original samplers and normalized mapping are unchanged. The validation horizon is480h; the archived planning objective used its original longer horizon. All outcomes were retained.

## Policy identities
- GA-post-evaluation-elitism: `46732e49c3afa0827cdf37543882b3ec3f06ab0a3f600eedd92162733fa5ee82`
- GA-previous-pure-random: `edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a`
- Impact-first: `d75ee1dc0fed0671b40d7f539d1e456ea42402105554cb1eb41ab3ec41bc9168`

## Mean population loss
- GA-post-evaluation-elitism: 33.009712128691h; median 33.012889810h.
- GA-previous-pure-random: 33.000890374631h; median 33.003729411h.
- Impact-first: 33.540545433356h; median 33.437565097h.

## Revised GA minus Impact-first
Mean -0.530833304666h; MCSE0.014425809953h. Pointwise95 [-0.558871772992,-0.502441498041]h; simultaneous95 Bonferroni [-0.563745824819,-0.498362537963]h. Paired median-0.394958972940h; improved1724/2000 (86.20%), worsened276, ties0. p05-1.626040291, p95+0.185042944, p99+0.654405084h; range[-5.627681239,+2.443535024]h. Mean worst5% difference+0.503377669h. This compares two fixed full policies, not the causal effect of elitism across optimizer seeds.

Loss decomposition changes: self+0.292778211731h, threshold+0.011271925069h, source-0.834883441465h. Sum-0.530833304666h; source/total signed ratio1.572779 (157.278%). This is a net signed accounting ratio, which can exceed100% when other components offset it; not a causal attribution.

Influence diagnostics (full untrimmed objective remains authoritative):
- Remove most favorable0% descriptively: mean-0.530833304666h; share of gross favorable benefit removed0.000%.
- Remove most favorable1% descriptively: mean-0.500735959227h; share of gross favorable benefit removed6.239%.
- Remove most favorable5% descriptively: mean-0.437866245100h; share of gross favorable benefit removed20.415%.
- Remove most favorable10% descriptively: mean-0.380890681229h; share of gross favorable benefit removed33.420%.
Leave-one-out mean range[-0.532321232794,-0.528283605849]h; sign reversals0/2000. Several-out rankings are sensitivity descriptions, not new confirmatory estimates.

## Revised GA minus GA-previous-pure-random
Mean +0.008821754060h; MCSE0.001149351752h. Pointwise95 [+0.006474522659,+0.011007624533]h; simultaneous95 Bonferroni [+0.006140493711,+0.011305551263]h. Paired median+0.007665213639h; improved657/2000 (32.85%), worsened1343, ties0. p05-0.028350769, p95+0.044168853, p99+0.156060259h; range[-1.448217941,+0.603253098]h. Mean worst5% difference+0.108114634h. This compares two fixed full policies, not the causal effect of elitism across optimizer seeds.

Loss decomposition changes: self+0.015016686579h, threshold+0.000518942441h, source-0.006713874961h. Sum+0.008821754060h; source/total signed ratio-0.761059 (-76.106%). This is a net signed accounting ratio, which can exceed100% when other components offset it; not a causal attribution.

Influence diagnostics (full untrimmed objective remains authoritative):
- Remove most favorable0% descriptively: mean+0.008821754060h; share of gross favorable benefit removed0.000%.
- Remove most favorable1% descriptively: mean+0.011094837644h; share of gross favorable benefit removed33.879%.
- Remove most favorable5% descriptively: mean+0.013265232344h; share of gross favorable benefit removed59.233%.
- Remove most favorable10% descriptively: mean+0.015210794159h; share of gross favorable benefit removed76.277%.
Leave-one-out mean range[+0.008524389706,+0.009550638350]h; sign reversals0/2000. Several-out rankings are sensitivity descriptions, not new confirmatory estimates.

## Hospital, timing and equity
All intervals below are descriptive pointwise95; lower mean population loss is not automatically improved hospital service, timing, typical realization outcome or equity.

### hospital_mean_normalized_burden_hr
- GA-post-evaluation-elitism: mean32.832066029145; median32.829092139.
- GA-previous-pure-random: mean32.796544004070; median32.790773012.
- Impact-first: mean33.065159016732; median33.046813983.

- Revised minusImpact-first: mean-0.233092987586; pointwise95[-0.261961822013,-0.204052194625]; paired median-0.097812213; unfavorable822/2000; p05-1.388909465,p95+0.524560171.

- Revised minusGA-previous-pure-random: mean+0.035522025075; pointwise95[+0.032796241106,+0.037916051046]; paired median+0.033732861; unfavorable1820/2000; p05-0.008253056,p95+0.086385863.

### T80_restricted_hr
- GA-post-evaluation-elitism: mean45.229925757531; median45.126073080.
- GA-previous-pure-random: mean45.196945454051; median45.077109552.
- Impact-first: mean45.381381457189; median45.244549694.

- Revised minusImpact-first: mean-0.151455699658; pointwise95[-0.213800584944,-0.090339922322]; paired median-0.056563692; unfavorable661/2000; p05-2.643833910,p95+1.783507609.

- Revised minusGA-previous-pure-random: mean+0.032980303480; pointwise95[+0.018245830004,+0.048144033925]; paired median+0.000000000; unfavorable256/2000; p05-0.199234570,p95+0.475593727.

### absolute_Q4_minus_Q1_hr
- GA-post-evaluation-elitism: mean3.170319710801; median2.962684879.
- GA-previous-pure-random: mean3.182604731595; median2.987847731.
- Impact-first: mean2.951212687686; median2.670044159.

- Revised minusImpact-first: mean+0.219107023115; pointwise95[+0.192777100506,+0.245967258938]; paired median+0.176409569; unfavorable1339/2000; p05-0.658907376,p95+1.246138349.

- Revised minusGA-previous-pure-random: mean-0.012285020795; pointwise95[-0.014825553884,-0.009844037092]; paired median-0.009647681; unfavorable799/2000; p05-0.088838462,p95+0.059719209.

### burden_gini
- GA-post-evaluation-elitism: mean0.200722426709; median0.202384078.
- GA-previous-pure-random: mean0.200371996066; median0.201751766.
- Impact-first: mean0.190739734106; median0.192392814.

- Revised minusImpact-first: mean+0.009982692603; pointwise95[+0.009454989594,+0.010516248832]; paired median+0.007665389; unfavorable1734/2000; p05-0.004121025,p95+0.031769644.

- Revised minusGA-previous-pure-random: mean+0.000350430643; pointwise95[+0.000300745618,+0.000405377949]; paired median+0.000342735; unfavorable1492/2000; p05-0.000587043,p95+0.001407530.

### signed_Q4_minus_Q1_hr
- GA-post-evaluation-elitism: mean-2.863432135938; median-2.911244604.
- GA-previous-pure-random: mean-2.878279335640; median-2.928401884.
- Impact-first: mean-2.571411592157; median-2.575586662.

- Revised minusImpact-first: mean-0.292020543781; pointwise95[-0.318224646400,-0.266479056929]; paired median-0.225169554; unfavorable563/2000; p05-1.373604693,p95+0.566702170.

- Revised minusGA-previous-pure-random: mean+0.014847199702; pointwise95[+0.012446082016,+0.017371722679]; paired median+0.011986752; unfavorable1244/2000; p05-0.055660376,p95+0.092110673.

### source_disconnected_dependency_integral_hr
- GA-post-evaluation-elitism: mean33.008229710234; median33.010166710.
- GA-previous-pure-random: mean32.999332999580; median33.002425278.
- Impact-first: mean33.538658227046; median33.436463478.

- Revised minusImpact-first: mean-0.530428516813; pointwise95[-0.558409246844,-0.502033782110]; paired median-0.393542813; unfavorable278/2000; p05-1.626040291,p95+0.185042944.

- Revised minusGA-previous-pure-random: mean+0.008896710654; pointwise95[+0.006551346728,+0.011069229165]; paired median+0.007771676; unfavorable1348/2000; p05-0.028288029,p95+0.044232379.

### source_dependency_T80_restricted_hr
- GA-post-evaluation-elitism: mean45.229925757531; median45.126073080.
- GA-previous-pure-random: mean45.196945454051; median45.077109552.
- Impact-first: mean45.381381457189; median45.244549694.

- Revised minusImpact-first: mean-0.151455699658; pointwise95[-0.213800584944,-0.090339922322]; paired median-0.056563692; unfavorable661/2000; p05-2.643833910,p95+1.783507609.

- Revised minusGA-previous-pure-random: mean+0.032980303480; pointwise95[+0.018245830004,+0.048144033925]; paired median+0.000000000; unfavorable256/2000; p05-0.199234570,p95+0.475593727.

### total_travel_hr
- GA-post-evaluation-elitism: mean27.089872328608; median27.086516804.
- GA-previous-pure-random: mean27.270018917765; median27.268228958.
- Impact-first: mean33.167514254011; median33.186635602.

- Revised minusImpact-first: mean-6.077641925403; pointwise95[-6.120910346916,-6.034409766678]; paired median-6.093911711; unfavorable0/2000; p05-7.656417407,p95-4.441563628.

- Revised minusGA-previous-pure-random: mean-0.180146589157; pointwise95[-0.212258769186,-0.147679552866]; paired median-0.176812888; unfavorable806/2000; p05-1.349128316,p95+1.016789460.

### makespan_hr
- GA-post-evaluation-elitism: mean77.422653559053; median76.640410161.
- GA-previous-pure-random: mean77.399082743372; median76.648169018.
- Impact-first: mean77.577231287286; median76.851463192.

- Revised minusImpact-first: mean-0.154577728233; pointwise95[-0.329702170097,+0.017062330970]; paired median+0.000000000; unfavorable998/2000; p05-7.300058916,p95+5.972780675.

- Revised minusGA-previous-pure-random: mean+0.023570815681; pointwise95[-0.007926096595,+0.054713014874]; paired median+0.000000000; unfavorable661/2000; p05-1.140801805,p95+1.161505871.

### mean_damaged_station_completion_hr
- GA-post-evaluation-elitism: mean33.170839097073; median33.152386940.
- GA-previous-pure-random: mean33.181488375311; median33.168819074.
- Impact-first: mean33.284048244216; median33.285083400.

- Revised minusImpact-first: mean-0.113209147143; pointwise95[-0.125704979424,-0.100658891033]; paired median-0.116597154; unfavorable647/2000; p05-0.598580710,p95+0.356851007.

- Revised minusGA-previous-pure-random: mean-0.010649278239; pointwise95[-0.012701058877,-0.008553273211]; paired median-0.009142614; unfavorable851/2000; p05-0.089410388,p95+0.064360813.

## Interpretations and boundaries
Hospital endpoint is an unweighted mean burden of hospital-associated tracts, not hospital supply or patient outcomes. Q1-Q4 means use the original SOVI quartile identities and population weights. SignedQ4-Q1 and the mean realizationwise absolute gap are different. Gini uses population-weighted tract burdens. SystemT80 uses native events and explicit480h censoring; makespan may extend beyond480h. Source-connected dependency mass is neither deliveredMW, electrical capacity, actual customers nor verified power flow. Simultaneous station completion and reconnection events are descriptive full-policy timing associations, not controlled station-level causal effects.

## Three distinct conclusions
Engineering correctness: all children are evaluated before conditional worst-offspring elite replacement. Optimizer performance: the previous paired seed study did not statistically demonstrate overall optimizer superiority. Restoration policy outcome: this experiment tests exactly one frozen revised sequence on new physical states; it does not retroactively prove algorithm superiority.

## Final recommendation
**RETAIN PRIOR VALIDATED CANDIDATE**. Registered decision uses both simultaneous population-contrast upper limits and checks for entirely adverse descriptive intervals on hospital burden,T80,absolute SOVI gap and Gini versus the prior pure-random GA. Entirely adverse flags: ['hospital_mean_normalized_burden_hr', 'T80_restricted_hr', 'burden_gini']. Unresolved intervals are not equivalence/noninferiority findings. The original mean-loss objective has not been changed; medians, unfavorable frequencies and influence sensitivity must accompany any author decision. No formal sequence is promoted.

## Reproducibility and preservation
Run `study.py setup`, `study.py engineering`, commit freeze and record `PREREGISTRATION_COMMIT.json`, then `study.py execute`, `analyze.py analyze`, `analyze.py package`, and `publish.py`. The original validation/evaluation modules in `_gaf12/src` are hash-locked, reused without editing. The inherited executor labels realization IDs with `standalone_prospective`; this is only an old identifier prefix, not an ILS strategy or a reused draw. Strategies and complete physical hashes are separately checked. SeedSequence namespace202610120701/r is new; bootstrap seed202610120702,20000 paired resamples. Prior source/draw identities were read for provenance, not outcome-guided selection. Original950 scientific files and862 staged items are verified before/after. The preexisting external manuscript path remains missing; the matching backup was checked read-only and neither restored nor declared authoritative. All conclusions remain conditional on this model, fixed hazard/resource, source proxy and population mapping; this is not empirical validation against observed grid recovery.
