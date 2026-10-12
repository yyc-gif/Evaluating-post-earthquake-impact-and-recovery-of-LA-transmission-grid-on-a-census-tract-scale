"""Reports from saved labels and authenticated frozen outputs, never new fits."""
import json
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from common import *

NOTICE = '**AUTHOR REVIEW - NOT FORMAL STAGE 7.**'
VARS = ['Init_Supply','Grid_Impact','Redundancy_HHI','B_480_hr','Delta_B_logistics','SOVI_SCORE','Population','BUILDVALUE']
NAMES = ['Initial service (%)','Spectral impact','Dependency HHI','B (deficit h)','Delta B (deficit h)','SOVI (0-100)','Population (persons)','Building stock (2022 USD million)']


def md(name, text):
    lp(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')


def table(data):
    return data.to_markdown(index=False, floatfmt='.4f')


def main():
    s=sources()
    d, labels, weights=inputs(s)
    d=frame('VERIFIED_INTERPRETATION_TRACT_VALUES.csv').set_index('tract_id').loc[d.index]
    rare=set(frame('THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').tract_id)
    p=frame('CLUSTER_ORIGINAL_UNIT_PROFILES.csv')
    c=frame('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv')
    r=frame('THIRTYFOUR_TRACT_IDENTITY_AND_STABILITY.csv')
    a=frame('INIT_ALGEBRAIC_DISTANCE_DECOMPOSITION.csv')
    stations=frame('STATION_INITIAL_STATE_AND_DAMAGE_SUMMARY.csv').set_index('substation_id')
    node=frozen(s,'Data/working_area_substations_with_fragility.csv',key='ID')
    core=frozen(s,'Data/source_nodes_core_expanded.csv',key='ID')
    stations['source_type']=core.source_type.reindex(stations.index).fillna('not retained Core')
    for col in ['LATITUDE','LONGITUDE','MAX_VOLT','MIN_VOLT','fragility_class']:
        stations[col]=node[col].reindex(stations.index)
    save('STATION_INITIAL_STATE_AND_DAMAGE_SUMMARY.csv',stations.reset_index())
    mapping=pd.read_csv(s.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',AUTH),dtype={'tract_id':str,'substation_id':str})
    W=mapping.pivot(index='tract_id',columns='substation_id',values='weight').fillna(0).reindex(index=d.index,columns=stations.index)
    station_contribution=W.mul(stations.mean_effective_initial,axis=1)
    attribution=pd.DataFrame({'tract_id':d.index,'Init_Supply':d.Init_Supply.to_numpy(),
        'rare34':d.index.isin(rare),'Q_weight':W['308581'].to_numpy(),
        'Q_initial_contribution':station_contribution['308581'].to_numpy(),
        'largest_contributor_id':station_contribution.idxmax(axis=1).to_numpy(),
        'has_positive_service':d.Init_Supply.gt(0).to_numpy()})
    attribution.loc[~attribution.has_positive_service,'largest_contributor_id']='none'
    attribution['Q_fraction_of_initial']=attribution.Q_initial_contribution.div(attribution.Init_Supply.where(attribution.has_positive_service))
    save('TRACT_Q_DEPENDENCY_AND_INITIAL_CONTRIBUTION.csv',attribution)
    separation=[]
    for model in SPECS:
        budget=weights['specifications'][model]
        z=(d[list(budget)]-d[list(budget)].mean())/d[list(budget)].std(ddof=0)
        for k in KS:
            for seed in SEEDS:
                y=labels[f'{model}__k{k}__s{seed}']
                for variable,w in budget.items():
                    t=float((z[variable]**2).sum()*w)
                    between=sum(int(y.eq(i).sum())*z.loc[y.eq(i),variable].mean()**2*w for i in range(k))
                    separation.append(dict(specification=model,k=k,seed=seed,coordinate=variable,
                        domain=weights['domains'][variable],squared_distance_budget=w,total_SS=t,
                        between_SS=between,within_SS=t-between))
    sep=pd.DataFrame(separation)
    sep['between_share']=sep.between_SS/sep.groupby(['specification','k','seed']).between_SS.transform('sum')
    save('DOMAIN_AND_COORDINATE_OBSERVED_VARIATION.csv',sep)
    realization=frame('THIRTYFOUR_REALIZATION_INITIAL_SERVICE.csv')
    q=realization.groupby('tract_id').initial_service.agg(['mean','median','min','max'])
    q['positive_sample_fraction']=realization.groupby('tract_id').initial_service.apply(lambda x:x.gt(0).mean())
    q['p90']=realization.groupby('tract_id').initial_service.quantile(.9)
    save('THIRTYFOUR_REALIZATION_SERVICE_DISTRIBUTIONS.csv',q.reset_index())
    reference=[]
    for v,n in zip(VARS,NAMES):
        scale=100 if v=='Init_Supply' else 1e-6 if v=='BUILDVALUE' else 1
        x=d[v]*scale
        reference.append(dict(variable=n,mean=x.mean(),median=x.median(),P10=x.quantile(.1),P90=x.quantile(.9)))
    save('COHORT_ORIGINAL_UNIT_REFERENCE.csv',reference)

    paragraphs=['# k=3 / k=4 / k=5: scientific comparison',NOTICE,
        'Authority: `'+AUTH+'`. All results below reuse registered labels; no new clustering, simulation, selection-score optimization or formal promotion. Seed 42 is the predeclared display reference, not a selected best seed. D1 means saved label 0, D2 label 1, etc.; IDs are specific to each specification/k/seed and are not formal Stage 7 IDs.',
        '## Cohort and reference distribution',
        'All 2,299 positive frozen-population tracts represent '+f'{d.Population.sum():,.0f}'+' people. Sixteen zero-population tracts remain excluded only from clustering; the study-wide service domain remains 2,315. All eight positive-population zero-housing tracts remain included. No old geometry exclusions, replacement population, imputation or new quartiles are introduced.',
        table(pd.DataFrame(reference)),
        'High/low descriptions refer to this same-cohort distribution, not a national hazard classification. Spectral impact is strongly skewed: its median is 0.000791 while its mean is 0.112209. SOVI is an existing FEMA national percentile, not a locally standardized vulnerability label.',
        '## Display profiles in actual units',
        'Cells below are **mean / median [P10, P90]**. Population is persons, stock is millions of 2022 USD; initial service is percent. Complete exact-precision profiles, original transformed input coordinates, extrema, population and original quartile counts for every one of the 60 registered conditions are in the two profile CSVs. BUILDVALUE is descriptive, not an input, in A; initial service is descriptive in minus-Init. Population below is original persons; the fitted coordinate is ln(1+persons).']
    for model in SPECS:
        for k in KS:
            selected=p[(p.specification==model)&(p.k==k)&(p.seed==42)]
            comm=c[(c.specification==model)&(c.k==k)&(c.seed==42)]
            rows=[]
            for _,cl in comm.iterrows():
                row={'Class':f'D{int(cl.diagnostic_cluster)+1}','Tracts':int(cl.n_tracts),
                    'Residents':int(cl.population),'Population share (%)':f'{cl.population_share*100:.2f}',
                    'Median persons':f'{cl.median_tract_population:.1f}'}
                for v,n in zip(VARS,NAMES):
                    x=selected[(selected.diagnostic_cluster==cl.diagnostic_cluster)&(selected.variable==v)].iloc[0]
                    sc=100 if v=='Init_Supply' else 1e-6 if v=='BUILDVALUE' else 1
                    row[n]=f'{x["mean"]*sc:.3f} / {x["median"]*sc:.3f} [{x.p10*sc:.3f}, {x.p90*sc:.3f}]'
                rows.append(row)
            paragraphs += [f'### {model}, k={k}',table(pd.DataFrame(rows)),
                table(comm[['diagnostic_cluster','Q1_tracts','Q2_tracts','Q3_tracts','Q4_tracts','hospital_incidence','added_zero_housing_tracts','median_lat','median_lon','p90_radius_km','maximum_quadrant_share']].rename(columns={'diagnostic_cluster':'Saved zero-based ID'}))]
    paragraphs += ['## What changes scientifically?',
        '**A/k3: three broad joint patterns.** D1 covers 63.30% of residents: low mean spectral importance (0.0154), lower-than-cohort B (30.87 h) and Delta B (1.38 h), but above-cohort SOVI (77.66) and population. D2 covers 30.66%: larger mean spectral importance (0.2742), B 37.73 h, Delta B 2.03 h, and lower mean SOVI 49.96. D3 covers 6.04%: much larger logistics penalty (12.45 h versus cohort P90 4.91 h), B 41.06 h, and lower dependency HHI 0.465; its SOVI 54.12 is mixed, not uniformly Q4. These are broad contrasts, not homogeneous resident experiences.',
        '**A/k4: principally adds a geographically local initial-state class.** The extra class is the same 34 Q-dependent tracts, not a new region-wide recovery/vulnerability regime. The 141-tract high-Delta class is unchanged. From A/k3 D1, 1,319 stay in the broad low-importance class and 32 join the rare class; two rare tracts come from D2. Eleven other D2 tracts switch to the broad class. A/k4 is defensible when explicit rare model-state geography is an author objective; its additional resolution is not independently justified by having four panels or by seed stability.',
        '**A/k5: adds a substantive structural distinction, with modest recovery separation.** D4 has 225 tracts/8.72% of residents, mean spectral impact 0.7909 (above cohort P90 0.4628), B 36.76 h, Delta B 1.94 h, SOVI 53.66. D3 has 558 tracts/21.00% of residents, impact 0.0578, B 35.48 h, Delta B 1.87 h, SOVI 36.58. Thus k5 distinguishes higher structural importance from a lower-SOVI moderate-recovery pattern; it does **not** establish five distinct recovery-time regimes. The high-Delta class is 148 tracts, and the Q-dependent 34 remain. This is a global repartition, not a purely hierarchical split: A/k4 D3 divides into 431, 215, 135 and 13 tracts across A/k5 D3/D4/D2/D5.',
        '**B/k3-k5:** the same broad disruption/recovery contrasts persist. B/k4 emphasizes the stock/SOVI boundary (mean stock 503 versus 754 million USD; mean SOVI 81.46 versus 38.67), while B/k5 again separates a high-impact class (229 tracts, impact 0.7839), a lower-SOVI class (607, SOVI 38.07), a high-Delta class (148, Delta 12.01 h), and the same rare 34. Stock is not a unique new outage-burden class; it changes membership and exposure emphasis.',
        '**A-minus-Init:** k3 already separates a 223-tract high-impact group (impact 0.7969) because remaining RQ1 budgets increase. At k4, two large groups chiefly differ in HHI (0.836 versus 0.476) rather than SOVI (68.54 versus 70.37); this is less balanced as a broad vulnerability typology. k5 separates HHI, SOVI, high impact and high Delta, with no standalone Q group.',
        '**B-minus-Init:** k3 resembles the A ablation; k4 separates high SOVI/lower stock (1,279) from lower SOVI/higher stock (644), high impact (230) and high Delta (146). k5 adds an HHI contrast within the higher-SOVI population. This explains model dependence; it is not evidence authorizing a new ablated primary model.',
        '## Membership, population, seed and geographic limitations',
        'All class means coexist with the reported P10-P90 ranges. Quartile counts and actual within-class distributions must be used instead of treating cluster centroids as attributes of every resident. The eight additional zero-housing tracts are distributed among ordinary multi-hundred-tract classes; none is in the rare 34, and no singleton class arises in these fits. Tract 06037980015 is in the rare group but is already in the residential cohort; its 9800 code alone is not a verified land-use designation.',
        'Five-seed ARIs are close to one for all candidates. Existing four-quadrant training perturbations are less stable; A/k3 median ARI is 0.705, A/k4 0.728, A/k5 0.701; B/k3 0.668, B/k4 0.698, B/k5 0.851. These coarse, saved train/predict stress tests are not new physical simulations, neighborhood-boundary validation or a k-selection rule. The rare group remains exact in three of four quadrant perturbations, but merges with other tracts when the southwest quadrant is withheld. The individual class geography is reported as official-point median latitude/longitude, radius and quadrant share; no unverified neighborhood polygons or spatial contiguity constraint is imposed.',
        '## Downstream descriptions, not independent validation',
        'Original Q1-Q4 membership is not recomputed and shares the SOVI input. T80, self/threshold/source burden decomposition, and Unconstrained B are alternative summaries of the same frozen realizations, not independent validation. Hospital-tract incidence uses an externally located facility flag, but is not all residents\' electricity-dependent health need. Additional policy trajectory evaluation was not necessary for the present interpretation and no policies were rerun. The reports do not establish causality between SOVI and recovery.',
        '## Recommendation',
        'Seven-variable A remains the better-aligned primary candidate. **k3 is the parsimonious recommendation for a broad three-RQ community comparison; k5 is a defensible conditional alternative when a separate structural-criticality class is essential.** k4 is specifically useful for local rare-source-state interpretation, not an automatic compromise or optimum. No k is promoted; the author must decide whether broad regional comparison or finer structural resolution is the intended use.']
    md('K3_K4_K5_SCIENTIFIC_COMPARISON.md','\n\n'.join(paragraphs))

    identity=frame('THIRTYFOUR_TRACT_NETWORK_SUMMARY.csv')
    contrib=frame('THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv')
    qcon=contrib[contrib.substation_id.eq('308581')]
    total=contrib.initial_service_contribution.sum()
    qshare=qcon.initial_service_contribution.sum()/total
    qstation=stations.loc['308581']
    md('THIRTYFOUR_TRACT_SOURCE_CONNECTIVITY_AUDIT.md',f'''
# Frozen network/source explanation of the 34 tracts

{NOTICE}

## Direct answer

The group has a demonstrable **model-internal** explanation: every tract's highest-weight station and largest initial-service contributor is **308581, STATION Q (HARBOR)**, a LADWP 138-kV station retained as a **Core `in_basin_generation_proxy`**. Mean dependency weight on Q is {qcon.normalized_weight.mean():.6f} (range {qcon.normalized_weight.min():.6f}-{qcon.normalized_weight.max():.6f}). Q supplies {qshare*100:.4f}% of the sum of their mean initial service; this is a service-contribution ratio, not electrical capacity or a power-flow allocation. Other aggregate contributions are Wilmington 1.8514%, Harbor Gen 0.7773% and Dock 0.1822%.

The frozen rule is F=1[f>=0.5], C=source connectivity within the F-eligible subgraph, and e=f*F*C. Q is itself a retained Core source. For its 40 eligible samples the saved path certificate is zero-hop, not proof that a remote supply corridor survived. The rare advantage is therefore the interaction of Q's **frozen sampled damage frequency**, its **assumed Core role**, and tract mapping. Less frequent severe damage alone does not explain the result.

## Realization-level evidence

Q's DS counts in 1,000 existing samples are [9,31,78,510,372] for DS0-DS4. The authenticated formal initial lookup is [1,0.5,0.09,0.04,0.03]; no legacy alternative lookup is substituted. Q reaches 0.5 in 40/1,000 samples, remains connected in all 40, and mean e is (9+31*0.5)/1,000=0.0245. Its raw mean f is 0.06308. Dock has a slightly larger raw mean (0.06356) but only 2/37 eligible samples are source-connected, so mean e is 0.001. Wilmington has 3/25 eligible samples source-connected and mean e 0.002. This contrast shows why raw station survival alone is insufficient.

Each rare tract's realization median initial service is **zero**. Positive-service frequency ranges from {q.positive_sample_fraction.min()*100:.1f}% to {q.positive_sample_fraction.max()*100:.1f}% (mean {q.positive_sample_fraction.mean()*100:.2f}%). Across the entire station system, only 114 of the 1,000 samples have any positive initial effective service. The group's mean tract availability of 0.018153 is a rare-event average; it does not mean every sample retains 1.8153% service, and is very low absolutely.

## Exact station and mapping audit

The 34 exact eleven-digit GEOIDs are in `THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv`. Their assigned positive-weight station count is 1-7 (median 3); average HHI is 0.581765 and average weighted spectral impact 0.028704. Mapping sums are one. Every tract-station weight and contribution is in `THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv`; each contribution is W_ri * mean(e_i(0)). All 2,299 Init_Supply values reproject from saved station e(0) with maximum absolute error 2.985e-16.

The same mechanism is continuous outside the rare cluster. Higher initial service increases with weight on Q, with other Core stations also contributing to some tracts. It is not a unique binary physical class; the K-means boundary partitions this continuous mapping/source outcome. `STATION_CONTRIBUTIONS_RARE_AND_OTHER_TRACTS.csv` records cohort and outside-group contributions, rather than assuming only these 34 receive Q service.

Frozen mean B decomposition for the rare group is 22.5303 h own-functionality loss + 0.8038 h threshold loss + 0.2670 h source-disconnection loss = 23.6011 h. The cohort's mean source-disconnection component is 4.3185 h. This is consistent with the retained source role and lower cumulative loss, but shares the simulation inputs and is not independent causal validation. Delta B is 2.1437 h, close to cohort mean 2.2877 h; the group is not uniquely insensitive to logistics.

## Identity and geography

The exact same 34 occur in A and B at k4 and k5 for all five registered seeds. All 23 top-1%-Init observations are among them. None of the eight added zero-housing positive-population tracts joins the group. Their total population is 124,158 (1.3694% of cohort population), Q4 membership is 13/34, and mean/median SOVI is 67.99/85.04; they are not uniformly low-vulnerability communities.

Official internal points occupy latitude 33.710708-33.790275 and longitude -118.329404 to -118.254908; P90 radius from the median point is 4.82 km. Three of four existing geographic perturbations preserve the exact group. With the southwest quadrant removed from training, A/k4 predicts a larger 207-tract class containing all 34 plus 173 others (Jaccard 0.1643); B/k4 predicts 211. A/k5 and B/k5 similarly merge into 206/210 tracts. All members survive that matching, but **the exact class does not**. Saved IDs and added/lost sets are explicit in the identity CSV. No new geographic fits were performed.

## Limits

The frozen Core assignment is a supply proxy, not independently verified islanding/generation availability. No alternate Core assignment, fragility, new damage sample, source propagation or power-flow test was run. Positive saved reachability is checked with functional-path certificates; the audit does not rebuild all negative reachability states. These results establish a specific model mechanism, not customer outage, feeder adequacy, electricity capacity, or real-world resilience. Original population upstream Census vintage remains unresolved even though frozen values are authenticated. Official points support locations and coarse quadrants, not municipal/neighborhood identification or contiguous class areas.
''')

    totals=a.groupby(['specification','algebraic_variant']).rare_centroid_global_between_SS.sum()
    leverage=a[(a.specification=='A')&(a.algebraic_variant=='registered')&(a.coordinate=='Init_Supply')].rare_centroid_global_between_SS.sum()/totals['A','registered']
    z=(d.Init_Supply-d.Init_Supply.mean())/d.Init_Supply.std(ddof=0)
    tail=d.Init_Supply.nlargest(23).index
    varshare=(z.loc[tail]**2).sum()/(z**2).sum()
    md('INIT_SUPPLY_SCALING_AND_ABLATION.md',f'''
# Init_Supply: model information versus numerical leverage

{NOTICE}

**Recommended status: retain with explicit rare-model-state interpretation and strong sensitivity limitations.** It is not an unqualified indicator of community resilience. It carries verified initial-state information that is distinct from cumulative recovery; its very sparse distribution nevertheless dominates the isolated 34-tract class.

There are {d.Init_Supply.eq(0).sum():,}/{len(d):,} exact zeros ({d.Init_Supply.eq(0).mean()*100:.4f}%). Near-zero counts and nonzero quantiles are in `INIT_DISTRIBUTION_AND_LEVERAGE.csv`; no zeros are replaced. The maximum is 0.0245, mean {d.Init_Supply.mean():.9f}, SD {d.Init_Supply.std(ddof=0):.9f}. Standardization maps zero to {z.min():.5f} and maximum to {z.max():.5f}. The highest 23 observations account for {varshare*100:.4f}% of Init's global centered sum of squares, despite only 1% of tracts. Under the A budget, they account for 6.9422% of total weighted global sum of squares.

## Algebraically isolate the two ablation effects, without fitting

Fix the exact 34 membership and the existing full-cohort standardization. Its weighted centroid separation from the global centroid in A is {totals['A','registered']:.6f}; Init accounts for {leverage*100:.4f}%. Dropping Init while leaving all other budgets fixed reduces it to {totals['A','drop_Init_fixed_other_budgets']:.6f}. Redistributing the RQ1 budget to Impact/HHI (each 1/6) increases the remainder only to {totals['A','drop_Init_RQ1_redistributed']:.6f}. This separates variable-presence leverage from reallocation: the latter adds 0.362195, about 1.535% of the non-Init remainder, not an explanation for the 89% collapse. B gives 216.818014, 23.653137 and 24.015332 respectively.

The fixed-other-budget calculation is an algebraic counterfactual (RQ1 budget 2/9), **not a newly fitted or proposed weighted model**. Actual registered minus-Init fits also change RQ1 budgets; their membership differences cannot be described as a pure deletion effect. Total standardized squared variation is 2,299 for full and redistributed models, versus 2,043.5556 when Init is omitted with other budgets fixed. Euclidean weights are square roots of the recorded budgets.

## Whole-partition versus rare-class leverage

The 89.11% value applies to the rare class centroid, **not the entire typology**. In A/k4/seed42, Init contributes 255.4444/2,299=11.11% of global weighted variation by design; between-class Init SS is 200.1248 and within-class SS 55.3197. Init accounts for 22.42% of all-coordinate between-class SS. Inside the rare class, its within-class SS is 6.9714 (approximately 31.32% of the rare class's total within-class variation). Other classes remain strongly structured by B, Delta and SOVI. All 60 per-coordinate total/within/between decompositions are in `DOMAIN_AND_COORDINATE_OBSERVED_VARIATION.csv`. Declared equal RQ budgets do not imply equal observed separation: for this A/k4 partition, RQ2 contributes about 55.08%, RQ1 31.05% and RQ3 13.87% of between-class variation. These are post-fit descriptions, not optimized weights.

## Other coordinates and original units

The group's mean B is 23.6011 versus 34.0537 h outside (about -2.00 cohort SD); this is meaningful modeled recovery contrast. Its mean Delta B (2.1437 versus 2.2898 h), SOVI (67.986 versus 66.486), log population, impact and HHI provide much weaker centroid contrasts. The non-Init weighted centroid separation remains nonzero but the registered ablations do not recover an independent 34-member class: A-minus/k4 best match retains 21 in a class of 946, B-minus/k4 retains 25 in 1,279. At k3 the main fits pool the rare state into broad classes. Stability alone is not construct validity.

## Decision and author approval

Keep Init provisionally because frozen Q-source/mapping evidence explains the rare survival condition. Treat k4/k5's 34-member class as **Q-proxy-dependent rare mean-initial-state geography**, not a general community recovery regime. k3 can retain the coordinate without making it a separate class. Moving Init to descriptive-only is a scientifically defensible alternative if the author's goal excludes local source-proxy state distinctions, but is not compelled merely by sparsity; adopting an ablated model requires explicit authorization. No transform, winsorization, jitter, new weighting, model fit, source-role validation or formal replacement is introduced.
''')
    dist=[]
    for name,mask in [('all',np.ones(len(d),bool)),('nonzero',d.Init_Supply.gt(0)),('rare34',d.index.isin(rare))]:
        x=d.loc[mask,'Init_Supply']
        dist.append(dict(subset=name,n=len(x),mean=x.mean(),median=x.median(),p10=x.quantile(.1),p90=x.quantile(.9),minimum=x.min(),maximum=x.max(),zero_count=x.eq(0).sum(),near_1e_6=int(x.le(1e-6).sum()),near_1e_4=int(x.le(1e-4).sum()),near_1e_3=int(x.le(1e-3).sum())))
    save('INIT_DISTRIBUTION_AND_LEVERAGE.csv',dist)
    cross=[]
    for k in KS:
        for seed in SEEDS:
            la,lb=labels[f'A__k{k}__s{seed}'],labels[f'B__k{k}__s{seed}']
            tr=frame('MEMBERSHIP_TRANSITIONS_AND_CLASS_MATCHING.csv')
            tr=tr[(tr.specification_a=='A')&(tr.specification_b=='B')&(tr.k_a==k)&(tr.seed==seed)]
            matched=tr.loc[tr.source_cluster==tr.target_matched_to_source,'n_tracts'].sum()
            cross.append(dict(k=k,seed=seed,ARI=adjusted_rand_score(la,lb),matched_unchanged=int(matched),changed=int(len(d)-matched),fraction_changed=(len(d)-matched)/len(d)))
    save('SEVEN_EIGHT_MATCHED_MEMBERSHIP_SUMMARY.csv',cross)
    md('SEVEN_VS_EIGHT_INTERPRETABILITY.md',f'''
# Seven versus eight: construct interpretation

{NOTICE}

**Recommend A as the primary candidate; retain B as an economic-stock extension, not a demonstrated improvement.** The previous authenticated audit finds log BUILDVALUE conditional linear R2=0.2804/VIF=1.3896 and random-tract spline CV R2=0.3177: stock is not a mechanical duplicate. It measures Hazus building stock in 2022 USD on 2020 Census support, NRI March 2023 v1.19, not power demand, household wealth or economic interruption damage. Statistical distinctness alone does not make it necessary for RQ3.

## k-specific interpretation

k3 retains three broad patterns with or without stock. k4 changes the large-class SOVI/stock boundary substantially (A/B seed42 ARI about 0.601); it strengthens a contrast between higher-SOVI/lower-stock and lower-SOVI/higher-stock tracts but adds no new unique stock-exposure class. k5 retains the same high-impact, lower-SOVI, high-logistics and Q-dependent patterns (A/B ARI about 0.801). B's 607-tract lower-SOVI class has mean stock 784 million USD versus A's comparable 558-tract class at 706 million. B/k5's high-impact class has 229 tracts versus A's 225. These changes are substantive membership reallocations, not merely renamed IDs; transparent Hungarian maximum-count matching and complete transition counts are provided.

{table(pd.DataFrame(cross).query('seed == 42'))}

## Budget confounding and interpretive limits

A-to-B both adds stock at 1/12 and halves the population budget from 1/6 to 1/12; SOVI stays 1/6 and RQ3 total remains 1/3. Therefore a change is not a pure stock-addition effect. The existing prior equal-RQ3 sensitivity is preserved but not promoted or newly refitted. Algebraic contributions cannot uniquely attribute new membership to asset information versus population-budget reduction. No tailored weights are selected for preferred profiles.

All 2,299 stock values are complete/positive, but upstream frozen population vintage is not externally authenticated. The eight zero-housing additions span stock from 7.24 million to 3.19 billion USD and do not generate an isolated rare class. The rare 34 are identical across A/B k4/k5, and remain exact after the saved asset-P99 leaveout training stress; they are not an extreme-stock artifact. High stock does not identify household wealth, and neither FEMA EAL/ALR nor RISK enters these candidates.

Seven coordinates sufficiently cover initial service, spectral importance, dependency concentration, total and extra logistics burden, social vulnerability and exposed residents. B is warranted only if the author explicitly broadens RQ3 to building-asset exposure and accepts that its consequences are not quantified. Its stronger RQ3 separation is partly mechanical from additional stock contrast, not validation. No new economic outcome, outage-loss estimate or formal typology is claimed.
''')
    md('K_SELECTION_AUTHOR_DECISION.md',f'''
# Scientific decision memo

{NOTICE}

## Six decisions answered

1. **Does the 34-tract group have a demonstrated network/service explanation? Yes, within the frozen model.** All depend most strongly on Q (308581); it provides {qshare*100:.4f}% of their aggregate mean initial service. As a retained Core proxy Q is directly source-qualified in its 40 eligible/1,000 samples. Each tract's sample-median service remains zero. This is not evidence of electrical resilience or verified islanded generation.
2. **Init status: retain with explicit rare-state interpretation and sensitivity limitations.** It provides authenticated initial-condition information, but explains 89.11% of the rare centroid separation. Source-role assumptions and standardization both matter. Do not promote an unqualified high-Init community label.
3. **k: A/k3 is the parsimonious broad-comparison candidate; A/k5 is a defensible finer structural alternative.** k4 principally extracts a local Q-dependent state and should be used only if that extra interpretation is an author objective. k5 adds a meaningful high-impact class but not five independent recovery regimes. There is no universal statistical optimum and no formal k is selected.
4. **Seven variables are sufficient for the stated three-RQ community focus.** BUILDVALUE adds valid asset exposure but does not clearly improve the intended service/vulnerability interpretation at k3-k5. Keep B conditional/descriptive unless economic stock exposure is an explicit author priority.
5. **Unstable/source-limited conclusions:** rare exact identity fails one coarse spatial training perturbation; wider class boundaries shift with stock and Init omission. Upstream frozen population Census vintage is unresolved. Core is a retained proxy and fragility/source-role alternatives were not tested. Geography uses official internal points, not verified neighborhood polygons. Cluster profiles, original SOVI quartiles and T80 share inputs and are not independent validation.
6. **Author decisions still required:** choose broad regional k3 versus finer structural k5 (or explicitly local-state k4); approve conditional Init retention and its wording; decide whether economic stock belongs in RQ3; acknowledge frozen source/population/geography limitations; then explicitly authorize any future formal Stage7 replacement and new figure/manuscript work. None is authorized or performed here.

## Equal-RQ weights

Retain the registered equal 1/3 domain budgets for this comparison as a transparent conceptual proposal, not a statistically optimized weighting. RQ1 Init/Impact/HHI=1/9 each, RQ2 B/Delta=1/6 each, RQ3 SOVI/population=1/6 each in A. B splits only the exposure sub-budget across people/stock. Within-domain and cross-domain correlation can reduce effective independent information; equal declared budgets do not guarantee equal realized between-class separation. The rare state illustrates why coordinate-level contributions and ablations must accompany this proposal. Evidence does not authorize numerical weight tuning here.

## Preservation and evidence scope

All 60 compared fits are saved registered results from `{AUTH}` (four specifications, k3/4/5, five seeds, existing n_init=50). No new fit, damage draw, recovery, scheduling, GA, source propagation, input change, quartile reassignment or formal promotion. Frozen setup: 2pc50 / Impact-first / C57_D1 / M1_UTILITY_003 / G1_BASELINE_050 / 480 h / 1,000 matched evaluation samples. The 950 protected scientific files and both prior audit packages are hash-checked unchanged. This is exploratory scientific interpretation, not an adopted new manuscript result. The bulk per-realization trajectories and integral archives are not Git-tracked; source-level reproduction requires the original manifest-bound read-only archive. A clean clone alone supplies the derived diagnostic extracts, not every original trajectory. The independently rechecked direct-community and Impact-first payloads are identical in this frozen case only.
''')
    md('README.md',f'''
# RQ-driven typology interpretation, 20261012

{NOTICE}

Start with `K_SELECTION_AUTHOR_DECISION.md`, then the full original-unit comparison and source audit. This package does not replace Stage7. Diagnostic class IDs are model-specific saved zero-based IDs (display D1=0). All GEOIDs retain eleven digits. Archived authority is `{AUTH}`.

## Reproduction

Use Python 3.12 and `pip install -r requirements-diagnostics.txt` (actual installed versions used for this review). Set `LA_GRID_FROZEN_SOURCE_ROOT` to the read-only archive containing authenticated `Formal_Experiment_20260923` trajectories/integrals and Git metadata. The local fallback is recorded in `common.py`; it is not an upstream scientific data path. `common.py` resolves exact Git blobs/LFS bytes and existing read-only caches; obtain retained inputs with Git LFS first. No archive download or regeneration is attempted if bytes are absent.

From this package directory run `python analyze_saved.py`, `python interpret_reports.py`, `python make_review_figures.py`, and `python verify_independent.py`. Analysis extracts existing station states and projects them linearly; it performs no new source gate, recovery or K-means. Report/figure steps use the verified extracts, not the model. Old seed/spatial stress results are reused. Independent QA asserts numerical identities, labels, physical hashes, exact cohorts, weights and preservation. Remote verification is separate, after scoped push. PDF review previews are rendered at 7.2-inch publication width and recorded in `VISUAL_QA.json`.

## Definitions and sources

Source/hash records list authoritative blobs and actual payload bytes. The prior package's frozen feature table, labels, preprocessing/weight JSON and stress tables are retained. Physical source records are 1,000 per-realization NPZ/JSON pairs authenticated against the frozen manifest and physical DS archive; the extracted NPZ is not a new simulation. `src/la_grid/revision/r1_source_gate.py` and `r1_realization_scheduling.py` define frozen semantics and are never executed here. Station IDs/coordinates/names/Core role and W come from frozen Data tables. B means realization-averaged normalized deficit hours over 0-480; Delta is matched Impact-first minus Unconstrained. Grid_Impact is W-weighted spectral connectivity loss, not the population-impact scheduling score. BUILDVALUE is NRI v1.19 total building stock, 2022 USD. SOVI uses frozen FEMA/CDC2020 percentile representation; original Q1-Q4 groups are preserved. Population upstream release remains unresolved.

The bulk per-realization trajectory/integral archive is not Git-tracked; a clean clone is insufficient for source-level extraction replay. This package retains authenticated initial-state extracts, profiles, labels for the 34 tracts and hash records so the interpretation can be inspected without silently regenerating missing source bytes. Full verification needs the original manifest-bound archive.

Every PDF/PNG is author-review diagnostics only. Profiles in actual-unit plots show means and P10-P90, not confidence intervals or independently validated community types. Geographic points do not imply neighborhood boundaries. No manuscript, numbered figure or formal simulation files are edited.
''')
    existing=frame('SOURCE_HASH_VERIFICATION.csv')
    save('SOURCE_HASH_VERIFICATION.csv',pd.concat([existing,pd.DataFrame(s.records)]).drop_duplicates().to_dict('records'))
    print('Interpretation reports written; no fits or simulations.')


if __name__=='__main__':main()
