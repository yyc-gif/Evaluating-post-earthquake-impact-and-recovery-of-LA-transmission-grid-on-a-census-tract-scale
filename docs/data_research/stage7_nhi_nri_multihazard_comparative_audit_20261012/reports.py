"""Evidence summaries; never selects or modifies formal Stage 7."""
from common import *
from audit_sources import HAZARDS, HAZARD_NAMES, NHI


def table(d, cols=None):
    if cols is not None:
        d = d[cols]
    return d.to_markdown(index=False, floatfmt='.6g')


def main():
    d = frame('FROZEN_COHORT_AND_COMPARATORS.csv', 'tract_id')
    reg = json.loads(lp(OUT/'FEMA_NCV_ADAPTATION_REGISTRATION.json').read_text())
    nr = pd.read_csv(lp(OUT/'sources/FEMA_NRI_v119_CA_FROZEN.csv'), dtype={'TRACTFIPS':str}, float_precision='round_trip').set_index('TRACTFIPS')
    raw = pd.DataFrame({h: (nr[h+'_AFREQ'] * nr[h+'_EXP_AREA']/nr.AREA).where(nr[h+'_AFREQ'].ge(0)&nr[h+'_EXP_AREA'].ge(0)&nr.AREA.gt(0)&(nr[h+'_EXP_AREA']/nr.AREA).le(1+1e-9)) for h in reg['hazards']})
    reg['final_sum_CA_complete14_reference_count'] = int(raw.notna().all(axis=1).sum())
    reg['registration_stage'] = 'Source-only pre-fit register; finalized reference count added without changing vector'
    dump('FEMA_NCV_ADAPTATION_REGISTRATION.json', reg)
    # Mechanical ID-storage repair of our own registered output; fitted values stay untouched.
    path=lp(OUT/'REGISTERED_CONDITIONAL_FIT_ARRAYS.npz')
    with np.load(path,allow_pickle=True) as source:
        arrays={k:source[k] for k in source.files}
    if arrays['tract_ids'].dtype.kind=='O':
        arrays['tract_ids']=arrays['tract_ids'].astype('U11')
        np.savez_compressed(path,**arrays)
    fitted = frame('CONDITIONAL_K_AND_STABILITY_RESULTS.csv')
    stab = frame('POLICY_SPATIAL_SEED_INIT_STABILITY.csv')
    size = frame('PER_CLUSTER_SILHOUETTE_AND_POPULATION.csv')
    evid = fitted.query("condition=='main'").groupby('k').agg(mean_WCSS=('WCSS','mean'),mean_silhouette=('mean_silhouette','mean'),sil_min=('mean_silhouette','min'),sil_max=('mean_silhouette','max'),negative_fraction=('negative_silhouette_fraction','mean')).reset_index()
    elbows = []
    for endpoint in [6,7,8]:
        part = evid.query('k<=@endpoint').copy()
        x = (part.k.to_numpy()-1)/(endpoint-1)
        y = (part.mean_WCSS.to_numpy()-part.mean_WCSS.iloc[-1])/(part.mean_WCSS.iloc[0]-part.mean_WCSS.iloc[-1])
        gap = (1-x)-y
        winner = int(part.iloc[np.argmax(gap)].k)
        for k,g in zip(part.k,gap):
            elbows.append(dict(endpoint=endpoint,k=int(k),normalized_chord_gap=float(g),maximum_gap_K=winner,meaning='Registered endpoint-dependent geometric bend; not physical optimum'))
    save('ELBOW_ENDPOINT_SENSITIVITY.csv', elbows)
    evid['fraction_WCSS_reduction_from_K1'] = 1-evid.mean_WCSS/evid.mean_WCSS.iloc[0]
    evid['relative_incremental_WCSS_reduction'] = 1-evid.mean_WCSS/evid.mean_WCSS.shift()
    for k in evid.k:
        for name,mask in [('seed',stab.test.eq('seed')),('geographic',stab.test.eq('geographic')),('policy_LOO_cohort',stab.test.eq('policy')&stab.condition.str.contains('without_')&stab.condition.str.endswith('__cohort')),('policy_LOO_fixed',stab.test.eq('policy')&stab.condition.str.contains('without_')&stab.condition.str.endswith('__fixed_main5'))]:
            vals = stab.loc[mask&stab.k.eq(k),'ARI']
            evid.loc[evid.k.eq(k),name+'_min_ARI'] = vals.min()
            evid.loc[evid.k.eq(k),name+'_mean_ARI'] = vals.mean()
        for suffix in ['cohort','fixed_main5']:
            val = stab.loc[stab.condition.eq('policy_plus_random__'+suffix)&stab.k.eq(k),'ARI']
            evid.loc[evid.k.eq(k),'plus_Random_'+suffix+'_ARI'] = val.iloc[0] if len(val) else np.nan
        classes = size.query('k==@k and seed==42')
        evid.loc[evid.k.eq(k),'smallest_class_tracts'] = classes.n_tracts.min()
        evid.loc[evid.k.eq(k),'smallest_class_population_share'] = classes.population_share.min()
    save('EIGHT_VARIABLE_K_EVIDENCE.csv', evid)
    comp = frame('CANDIDATE_MEMBERSHIP_COMPARISONS.csv')
    nc = frame('FEMA_NCV_NORMALIZED_COMPONENTS.csv','tract_id')
    div = json.loads(lp(OUT/'EFFECTIVE_HAZARD_DIVERSITY.json').read_text())
    geo = frame('COLUMBIA_NHI_2010_TO_2020_GEOGRAPHY_QA.csv','tract_id')
    gap = geo.official_land_supported_fraction.lt(1-1e-8)
    raw_nhi = frame('COLUMBIA_SOURCE_ATTRIBUTE_RECORDS.csv','source_2010_GEOID')
    transfers = frame('COLUMBIA_NHI_TRANSFERRED_VALUES.csv','tract_id')
    nri_raw = frame('FEMA_NCV_HAZARD_COMPONENT_VALUES.csv','tract_id')
    cf = frame('FEMA_NCV_EFFECTIVE_HAZARD_CONTRIBUTIONS.csv')
    # Signed covariance attribution is an algebraic diagnostic, not negative hazard weighting.
    cparts = []
    for name,values in [('Columbia_dominant_published_sum',raw_nhi.reindex(transfers.dominant_source)[[h+'_hazcat5' for h in NHI]].fillna(0).set_axis(d.index)),('FEMA_NCV14',nc[reg['hazards']])]:
        total = values.sum(1); variance = total.var(ddof=0)
        for col in values:
            v = values[col]
            cparts.append(dict(candidate=name,hazard=col,mean_component=v.mean(),sd_component=v.std(ddof=0),zero_count=int(v.eq(0).sum()),covariance_share=((v-v.mean())*(total-total.mean())).mean()/variance,missing_to_zero_for_reconstruction_only=name.startswith('Columbia')))
    save('CANDIDATE_LOCAL_COMPONENT_ATTRIBUTION.csv', cparts)
    comparisons = [
        dict(candidate='Columbia NHI v2.0 original14',earthquake=True,construct='Published ordinal category sum',geography='2010; transferred via official land relation',valid_published_numbers=2299,fully_supported_targets=0,direct_SOVI_assets_losses=False,gate='EXPLORATORY_ONLY',limitation='Unknown/no-hazard conflation,11 land gaps; USFS wildfire RPS uses generic structure response, not actual monetary stock'),
        dict(candidate='FEMA_NCV14_CA_v119',earthquake=True,construct='Relative multi-hazard geographic exposure screening index',geography='Native frozen2020 tract IDs',valid_published_numbers=2299,fully_supported_targets=2299,direct_SOVI_assets_losses=False,gate='PASS_NATIVE_FULL_COHORT (selected modeled inputs only)',limitation='14-hazard CA-normalized tract extension; four all-null hazards excluded; heterogeneous native measures; minimum defaults; no full original physical-grid validation'),
        dict(candidate='Williams2024 exact county nine-set',earthquake=True,construct='Published frequency-area/min-max method; exact aggregate unspecified',geography='County empirical implementation',valid_published_numbers=0,fully_supported_targets=0,direct_SOVI_assets_losses=False,gate='FAIL_SOURCE_RECONSTRUCTION',limitation='Published PDF and accepted XML do not enumerate aggregate nine; no public output workbook located'),
        dict(candidate='CDC RPL_CBM',earthquake=False,construct='Selected climate-burden national percentile',geography='Published2020 tract geography',valid_published_numbers=2299,fully_supported_targets=0,direct_SOVI_assets_losses=False,gate='FAIL_CONSTRUCT for new earthquake-inclusive objective',limitation='Climate-only, unresolved component flags and source-zero substitutions; reused qualified comparator only')]
    save('NHI_NCV_CBM_CANDIDATE_COMPARISON.csv',comparisons)
    default=nr.loc[d.index,'LNDS_AFREQ'].eq(.01)
    save('FEMA_DEFAULT_MASK_MISSINGNESS_DIAGNOSTIC.csv',[dict(hazard='LNDS',rule='Treat released .01 minimum as unknown in diagnostic only; not inserted into fitted matrix',affected_tracts=int(default.sum()),affected_population=int(d.loc[default,'Population'].sum()),remaining_full14_complete_tracts=int((~default).sum()),rank_or_clustering_recomputed=False,interpretation='Literal default masking would destroy full-cohort support. No claim of fully observed hazards.')])
    fits=np.load(lp(OUT/'REGISTERED_CONDITIONAL_FIT_ARRAYS.npz'));index={k:i for i,k in enumerate(fits['keys'])}
    x=np.load(lp(OUT/'REGISTERED_CONDITIONAL_MATRICES.npz'))['main']
    labels=fits['labels'][index['NCV14__main__k4__s42']]
    ss=[]
    for c in range(4):
        mask=labels==c;center=x[mask].mean(0)-x.mean(0)
        ss.append(dict(cluster=c,n_tracts=int(mask.sum()),population=int(d.loc[mask,'Population'].sum()),Init_centroid_squared_fraction=center[0]**2/(center@center),hazard_centroid_squared_fraction=center[-1]**2/(center@center),mean_Init_Supply=d.loc[mask,'Init_Supply'].mean()))
    save('K4_RARE_STATE_SCALING_QA.csv',ss)
    rare=read(reader(),'docs/data_research/stage7_rq_typology_interpretation_20261012/THIRTYFOUR_TRACT_NETWORK_SUMMARY.csv','tract_id')
    members=d.loc[labels==0,['Population','Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta']].copy()
    members['prior34_Q_group']=members.index.isin(rare.index)
    save('K4_INITIAL_STATE_EXCEPTION_GEOIDS.csv',members.reset_index())
    from scipy.spatial.distance import pdist
    zpop=(d.log1p_Population-d.log1p_Population.mean())/d.log1p_Population.std(ddof=0)
    hv=frame('FEMA_NCV_CANDIDATE_VECTORS.csv','tract_id').reindex(d.index).FEMA_NCV14_CA_v119
    zh=(hv-hv.mean())/hv.std(ddof=0)
    removed=pdist(zpop.to_numpy()[:,None],'sqeuclidean')/12
    added=pdist(zh.to_numpy()[:,None],'sqeuclidean')/12
    original=np.load(lp(OUT/'FROZEN_COMPARATOR_WEIGHTED_MATRICES.npz'))['P2__published']
    full=pdist(x,'sqeuclidean');before=pdist(original,'sqeuclidean')
    np.testing.assert_allclose(full-before,added-removed,atol=1e-12,rtol=0)
    save('ALGEBRAIC_POPULATION_HAZARD_REALLOCATION.csv',[dict(comparison='P2 to H2-NCV14',pairs=len(full),identity='Distance2_new-Distance2_P2 = (zHaz_i-zHaz_j)^2/12 - (zPop_i-zPop_j)^2/12',max_identity_error=np.max(np.abs((full-before)-(added-removed))),mean_added_hazard=added.mean(),mean_removed_population=removed.mean(),mean_net_change=(full-before).mean(),p10_net_change=np.quantile(full-before,.1),p90_net_change=np.quantile(full-before,.9),interpretation='Feature addition and exposure-sub-budget reallocation jointly change pair geometry; equal average budget does not imply same partitions')])
    k4 = evid.query('k==4').iloc[0]
    profile = frame('ORIGINAL_UNIT_CLUSTER_PROFILES.csv').query('k==4').pivot(index='cluster',columns='variable',values='mean').reset_index()
    classes = size.query('k==4 and seed==42')[['cluster','n_tracts','population','population_share','rare34_members','zero_housing_positive','low_population100_or_less']]
    profile = classes.merge(profile,on='cluster')
    save('K4_COMPACT_ORIGINAL_UNIT_PROFILE.csv',profile)
    bends = sorted({r['maximum_gap_K'] for r in elbows})
    source_links = """- [Columbia NCDP official NHI v2.0](https://ncdp.columbia.edu/us-natural-hazards-index/)
- [Verified Columbia ArcGIS layer77](https://services2.arcgis.com/IsDCghZ73NgoYoz5/ArcGIS/rest/services/Hazards_Index_Sum/FeatureServer/77)
- [Census California 2010-to-2020 tract relationship](https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_st06.txt)
- [Matching FEMA March2023 v1.19 technical documentation, official Ohio mirror](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)
- [Williams, Summers and Harwell2024](https://doi.org/10.3390/su162310778)
- [Publisher's archived PDF](https://mdpi-res.com/d_attachment/sustainability/sustainability-16-10778/article_deploy/sustainability-16-10778.pdf)
"""
    md('FROZEN_POLICY_AND_SOURCE_AUTHORITY.md',f"""# Frozen evidence dependencies

All seven existing coordinates and population/quartile descriptors are checked against {AUTH}. Frozen comparator matrices and saved fits are copied exactly from stage7_final_eighth_hazard_coordinate_20261012, not recalculated from new physical evaluations. The MP and policy-reference packages at this same authority contain FROZEN_EVENT_VERIFICATION.csv, POLICY_PAIRING_QA.json, POLICY_REFERENCE_SOURCE_AND_PAIRING_QA.md and the original source manifests. No new pairing, station order, mapping, damage, gate, duration or travel input is constructed in this package.

The 1000 frozen evaluation identities and physical/schedule/event archive integrity were established in those commit-bound packages. This task independently verifies the exact inherited feature bytes and their source hashes, rather than repeating a full1000-archive integration or generating new trajectories. Manifest-bound local archives remain external clean-clone dependencies. Their prior QA is inherited evidence, not a new physical validation claim.

The source lookup helper is an exact committed copy, rehydrated in support/ because an earlier disposable reader worktree was no longer available. This does not modify or restore that old worktree. All original950 scientific files and current unrelated staged/untracked work are separately hash/status checked. Physical source layers underlying both index providers are not all reprocessed here; only actual released factors, metadata, geometry and documented assumptions are verified.
""")
    md('COLUMBIA_NHI_V2_SOURCE_AND_FORMULA.md',f"""# Verified Columbia NHI v2.0

The actual provider dataset was retrieved, not inferred from a historical endpoint. The official NCDP page links Experience app fda2d684cd3f4ed5b802818a298d1b1a; archived app data links webmap1ddc2479ea4b4fe491fd776843c73cf6, whose layer resolves to FeatureServer/77, item ecdfbee171bb4224b7c47862c6e484a5. Layer description specifies 2010 Census tracts. Ancillary POP2020 is not a geometry-vintage declaration.

The OID inventory has2343 LA features. Twenty-four100-OID GeoJSON requests reproduce exactly that inventory without result-offset pagination, simplified geometry or silent duplicate removal.400-ID query failures are preserved as failed responses, not data. All fourteen raw indicator values, category numbers, textual labels, original geometry and hazsum5 are archived. Published sum equals sum of available categories, with NULL contributing zero only to reconstruct provider arithmetic: maximum absolute error0.

Ratings represent1-5 ordinal severity bins, with explicit0 tsunami footprint values. No-data and no-hazard both affect the provider sum as zero; these conditions cannot be inferred separately from a NULL rating. Original records remain unmodified. Sources/years are preserved in the official app documentation tables1/2. Earthquake categories are saturated:2341 of2343 source tracts are5, two are4. Local winter class is constant1; drought is5 in2307 source tracts. Locally varying heat, flood, landslide and wildfire categories account for much of the summed variation; precise signed covariance shares are in CANDIDATE_LOCAL_COMPONENT_ATTRIBUTION.csv, not a declaration of independent hazard importance.

Wildfire RPS combines burn probability with a generic response of a hypothetical structure, not actual house counts, income or monetary building value. Nevertheless this is not a pure physical-intensity coordinate. See archived USFS source. The broader NHI omits social/resilience/value adjustment but retains heterogeneous classification and generic response assumptions.

{source_links}
""")
    md('COLUMBIA_NHI_MISSING_ZERO_SEMANTICS.md',f"""# Columbia missingness and geographic gate

NULL is retained in all source fields. Provider arithmetic uses zero for unknown or absent hazard, but a summed numerical score is not full fourteen-hazard observation. None of2299 target tracts has fourteen non-null source components. Volcano and hurricane are NULL in every LA source tract; hail, tornado and damaging-wind records are mostly NULL. Tsunami has explicit raw/category0 outside its modeled footprint; it indicates the layer's geographic exclusion, not proof of physically impossible tsunami. Text label NaN on those numeric zeros is retained separately.

Official TIGER2010 has2346 LA tracts, whereas the NHI service has2343. Missing donors06037990100,06037990200,06037990300 have zero land in the archived2010 TIGER edition. The Census2020 relationship's updated2010 geography assigns small land parts to these codes; the two editions must not be treated as geometrically identical. Eleven targets lack some official donor land, representing{int(d.loc[gap,'Population'].sum()):,} residents. Lowest supported land fraction is{geo.official_land_supported_fraction.min():.6f}. These eleven are retained and flagged, not dropped or filled. The ordinal land-average estimate is unavailable on inadequately covered targets; dominant donor values remain explicitly estimates.

Exact identifier matches:{int(geo.exact_GEOID_match.sum())}/2299. Relationship types:\n\n{table(geo.relation_type.value_counts().rename_axis('relationship').reset_index(name='tracts'))}

All polygon intersections use equal-area EPSG3310; invalid polygons alone use make_valid, not buffer or arbitrary clipping. Geometric total-area overlaps, union coverage and partition excess are reported separately from the official LAND-area relationship used for transfer. Identical identifiers do not imply identical boundaries. Dominant-land-source categories and fractional class compositions are screening transfers, not reconstructed2020 physical hazard intensity. Area-averaged ordinal values are researcher diagnostics only.

Admission: EXPLORATORY_ONLY for original14 score. Do not fit this vector to the primary cohort or repair NULL by assumed zero. A missingness-aware sum of seven commonly complete layers would change the declared index and still inherit source/projection uncertainty; no replacement index is promoted here.
""")
    md('FEMA_NRI_SOCIAL_ASSET_LOSS_SEPARATION.md',"""# What is removed and what is retained

NRI's final risk combines expected losses with a community factor based on social vulnerability/resilience. Risk score is a ranking of that construct. Numerical division RISK_VALUE/CRF_VALUE reproduces EAL_VALT within release rounding tolerance (FEMA_SOCIAL_FACTOR_REMOVAL_NUMERICAL_QA.csv): it does not remove asset, population or loss-model inputs. EAL still encodes exposed building/population/agricultural stock and historical/modelled consequence assumptions. ALR_NPCTL is not a pure occurrence-frequency measure.

The new screening operator uses only each released *_AFREQ, *_EXP_AREA and AREA. It does not read SOVI, RESL, CRF, BUILDVALUE, POPULATION, EAL, HLR or Risk in constructing the hazard coordinate. Frozen study population is used only as the separate seventh coordinate and for post-fit resident coverage. No monetary building exposure or modeled service outcome enters the eighth coordinate.

Geographic EXP_AREA nevertheless inherits FEMA's widespread, susceptible or representative footprint conventions, and block/fishnet/county spatial aggregation. AFREQ can be an observed-event model, event-day estimate, minimum default or modeled probability surrogate. Independence from direct monetary/social adjustment does not establish physical measurement validity or independence among hazard processes.

Earthquake is special: March2023 documentation PDF151-155 describes a USGS100-year minor-damage probability surface, numerical conversion and area aggregation. This released surrogate is not CGS PGA-2pc50, a historical event count or a independently verified annual station-failure probability. Earthquake EAL instead uses Hazus P366 methodology; it is not reconstructed by substituting the frequency-area factor. The exact raw source raster was not acquired for pixel-level validation.
""")
    md('WILLIAMS_2024_NCV_METHOD_REPLICATION.md',f"""# Published-method versus exact implementation

Both the official publisher's13-page PDF and EuropePMC accepted XML were acquired, hashed and read. Sections2.1-2.3 on publisher pages4-5 specify the hazard factor:

NCV_h = AFREQ_h * (EXP_AREA_h / AREA).

Then independently min-max each hazard, sum normalized hazards, and min-max the sum. Empirical analysis is county-level; the denominator definition also mentions Census tracts, but this does not validate tract aggregation. The individual earthquake map is Figure7. Published comparisons address susceptible-area fractions, individual hazard factors, histograms and maps, not our electricity-restoration typology.

Exact aggregate replication is NOT achieved: the Methods says nine combined hazards but Table1 lists all18 available NRI types, without an explicit aggregate-nine list. The original normalization universe/extrema, missing/not-applicable and zero-range rules and a reproducible county result workbook are not supplied in acquired materials. The published Data Availability text points to a local network-drive location rather than a usable public file. No supplementary numerical table or exact source-version snapshot was acquired. The paper's source access date is January2024, whereas our input remains frozen March2023 v1.19. Reference to CRSI's hazard set is not permission to guess the aggregate list.

The mathematical frequency-area operator is independently reproduced on actual frozen tract rows (WILLIAMS_FACTOR_REAL_SOURCE_EXAMPLES.csv), including ERQK, WFIR, RFLD and HWAV. These examples are real source calculations, not falsely attributed published county examples. The fourteen-hazard extension and California normalization are separately registered before fitting. Original exact-nine implementation stays FAIL_SOURCE_RECONSTRUCTION; the tract extension has a qualified full-cohort modeled-input gate.

{source_links}
""")
    md('FEMA_NCV_TRACT_SCALE_ADAPTATION_AND_LIMITATIONS.md',f"""# Registered tract-scale fourteen-hazard extension

Exact input: Data/NRI_Table_CensusTracts_California.csv from authority {AUTH}; original payload copied byte-for-byte and verified by SHA256. NRI_VER is Mar-23 for9106 records. All2299 frozen eleven-digit tract IDs match. Four study hazards (AVLN,HRCN,ISTM,VLCN) have entirely null source factors and are omitted, NOT changed to zero. The fourteen retained hazards are {', '.join(reg['hazards'])}. This set follows complete compatible source support before clustering, not silhouette or preferred labels. CWAV is a valid local zero-frequency constant, not missing; thirteen components vary locally.

For every hazard require nonnegative actual AFREQ/EXP_AREA, positive AREA and area fraction<=1 within1e-9 numerical tolerance. No source fraction is clipped. All18 study field factors and source periods appear in the raw register; native frequencies include events/year, event-days/year and probability surrogates. Multiplying by geographic fraction is not a probability of compound disaster or electrical failure.

Hazard-level min-max uses actual valid rows in the frozen9106-tract California table. Final sum min-max uses{reg['final_sum_CA_complete14_reference_count']} rows with all14 valid components, never partial sums with NULL filled zero. Reference extrema are saved. National frozen-v1.19 county/tract ZIP retrieval failed with actual failure responses archived; national normalization and the original paper scale are NOT verified. LA-only sensitivity omits constant CWAV explicitly instead of dividing by zero. Changing hazard-specific normalization alters implicit component scales; final affine score normalization alone cancels under cohort z-scoring.

Earthquake AFREQ has1695 distinct study values, but the factor after area fraction ranges{nri_raw.ERQK_NCV_raw.min():.8f}-{nri_raw.ERQK_NCV_raw.max():.8f}; normalized earthquake background is high and its local covariance share is{div['earthquake_covariance_share']:.4%}. For example06037576602's relatively high frequency is attenuated by the partial exposed area; do not equate raw frequency with this factor. Local earthquake variation exists, but deleting it barely changes K4 memberships. It is a directly included component, not a dominant source of local differentiation.

RFLD's positive frequency is the same inherited LA county estimate for439 tracts;1860 have recorded zero factor. Local flood differences mostly reflect the footprint. LNDS uses a0.01 minimum where applicable; documentation's main-section105.8-year denominator conflicts with AppendixB2010-2021 and source rows whose event/frequency ratios suggest12 years. This unresolved documentation/source mismatch remains disclosed, not repaired. Event-day weather measures may share source models or coarse spatial supports. Masking default-dependent LNDS is evaluated only as a non-fitted missingness diagnostic, without cohort loss or imputation.

This is FEMA_NCV14_CA_v119: a researcher-derived relative multi-hazard geographic exposure screening index, not an official FEMA field, not national overall risk, not exposure-weighted monetary loss, and not a simulation of wildfire/flood compound outages.
""")
    md('EXECUTIVE_SCIENTIFIC_DECISION.md',f"""# Best qualified earthquake-inclusive candidate

**Recommend FEMA_NCV14_CA_v119 as the eighth-coordinate AUTHOR-REVIEW candidate**, subject to explicit approval of the14-hazard tract extension and California reference normalization. It has native frozen2020 identifiers, no missing/imputed selected inputs on2299 tracts, no direct social/monetary/loss adjustment, and direct earthquake plus non-earthquake content. This is not a faithful full Williams county-nine replication or an official FEMA score.

Columbia's actual data and metadata were retrieved and published sums exactly reproduced. It is weaker for this primary application: missing/no-hazard are conflated, no target has full14 component support, eleven2020 targets have missing donor land, and earthquake classes largely saturate. CDC CBM remains a useful published climate comparator but fails the new direct-earthquake inclusion requirement. Do not concatenate PGA and CBM to bypass either issue.

Local NCV variation is mainly heat wave33.73%, hail31.07% and strong wind24.71% by signed covariance attribution. Positive-share participation ratio is{div['positive_covariance_participation_ratio']:.3f}; this is a contribution diagnostic, not proof of independent hazards. Earthquake supplies high baseline normalized score but little local membership influence. The coordinate adds a distinct geographic screening construct beyond first7 (conditional linear R2=.1817,VIF1.222); nonlinear random-fold R2=.6266 versus geographic-quadrant R2=-.2114 shows strong geographic co-occurrence and weak spatial transfer, not independence or causality.

**K4 is the strongest qualified review resolution within this registered NCV space**, not a formally adopted optimum: mean silhouette{k4.mean_silhouette:.6f}, seed-minARI{k4.seed_min_ARI:.6f}, geographic-minARI{k4.geographic_min_ARI:.6f}. Normalized endpoint-chord bend for K1-6/7/8 favors {bends}, while silhouette favors4. K3 remains a coarser defensible interpretation; K5 is notably sensitive to seeds, heat removal and regional normalization. The elbow is smooth/endpoint dependent rather than a sharp scientific threshold.

Policy-set LOO with cohort scaling has K4 minimumARI{k4.policy_LOO_cohort_min_ARI:.6f}; fixed-main5 scaling gives{k4.policy_LOO_fixed_min_ARI:.6f}. Multi-policy summaries are therefore not policy-neutral. Geography is only four registered median-axis blocks, not spatial external validation. K4 retains a38-tract initial-state exception containing all34 prior Q tracts; it is not a physically validated resilient community class. Mean initial service in that class is1.7306%, still near-total modeled outage. Removing Init with registered RQ1 redistribution changes K4 strongly (ARI=.29425), so this dependence is substantive.

All2299 positive-population tracts and9066522 residents are represented; eight positive-population zero-housing tracts remain and do not define the38-tract rare class. Original2315-tract study-wide outcomes, quartiles and formal Stage7 are untouched.

At the displayed seed42/K4 fit, the hazard coordinate supplies2.452% of total between-class squared separation; realized RQ1/RQ2/RQ3 shares are33.09%/56.23%/10.68%, despite equal assigned domain budgets. Equal input budgets do not guarantee equal realized separation and are not tuned to enforce it. Agreement with P2 isARI=.90266 (76 tracts/2.625% of residents reassigned after display matching); with H2-CBM it isARI=.92540 (56 tracts/2.615% residents). These are controlled geometric comparisons, not evidence that the NCV model delivers better physical predictions. About78.70% of the rare class centroid's squared displacement is Init-driven. The algebraic population/hazard budget diagnostic explicitly separates their competing pair-distance terms without fitting a new model.

Author decisions: approve selected14/CA-normalized screening construct rather than national exact-nine replication; approve H2 budgets; choose K3 or qualified K4 after reviewing rare-state and policy sensitivity. Resolve/accept FEMA earthquake scale and LNDS denominator/source conventions; obtain national frozen snapshot and original county workbook for a stricter replication. No formal promotion is authorized or performed.

## Native-unit K4 profiles

Class IDs are model-specific ascending main5 total deficit, not formalStage7 IDs. Means reference the same2299-tract cohort; complete mean/median/P10/P90/ranges are in ORIGINAL_UNIT_CLUSTER_PROFILES.csv. Burdens are equivalent full-service-deficit hours; SOVI is0-100; NCV is0-1 California-relative.

{table(profile,['cluster','n_tracts','population','population_share','Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','Population','FEMA_NCV14_CA_v119'])}

Class0 is the rare higher-but-still-low initial-state group and has a relatively large additional logistics deficit. Class1 combines relatively high SOVI and population with lower spectral grid importance and logistics increment. Class2 has intermediate baseline burden and a relatively larger constrained increment. Class3 has the largest baseline burden and higher spectral grid importance with lower SOVI than class1. These are descriptions of fitted coordinates, not independent validation or universal community labels.

## K evidence

{table(evid,['k','mean_WCSS','mean_silhouette','seed_min_ARI','geographic_min_ARI','policy_LOO_cohort_min_ARI','smallest_class_tracts'])}

{source_links}
""")
    md('FINAL_MULTIHAZARD_COORDINATE_AUTHOR_DECISION.md',"""# Author decision, not formal replacement

The best qualified earthquake-inclusive candidate is FEMA_NCV14_CA_v119, with the existing H2 squared-distance budgets. Review K4 as the clearest current detailed resolution, with K3 a coarser alternative. See EXECUTIVE_SCIENTIFIC_DECISION.md and the endpoint/silhouette/robustness records. Neither model nor K is promoted.

Approve the14-hazard native-tract extension and California normalization explicitly; it is not the unresolved published county-nine aggregate. Accept or resolve the documented heterogeneous physical supports, minimum-frequency assumptions, earthquake probability-surrogate interpretation and LNDS denominator inconsistency. Decide whether the Q-driven rare state is a separate reported type or a limitation of primary interpretation. The large minus-Init and moderate policy/geographic sensitivity must remain visible. All data fields and model identities preserve the original scientific authority; no broad search or optimized weights is performed.

Obtaining a full frozen nationalv1.19 input and the paper's public numerical implementation would improve source/normalization certainty. Columbia requires disambiguated component NULLs and robust official2020 geographic support before competing as a14-hazard primary vector. CBM can remain climate context only. No unverified seismic/climate hybrid is proposed.
""")
    md('EIGHTH_VARIABLE_METHODS_AND_LIMITATIONS.md',f"""# Proposed Methods only

A relative geographic multi-hazard screening coordinate was derived from frozen FEMA NRI March2023 v1.19 frequency and impacted-area factors following the frequency-area operator of Williams et al.(2024). Fourteen hazard types had complete compatible released factors for all2299 positive-population tracts, including earthquake. For each hazard, annualized frequency was multiplied by the fraction of tract area represented by its released footprint. Hazard-specific factors were min-max scaled against their valid frozen California records, equally summed, and the sum min-max scaled using complete fourteen-component California records. Source-null hazards were excluded from the declared set, not replaced by zero. This tract-scale fourteen-hazard/California-reference extension is researcher-derived, not an official FEMA risk field or exact replication of the original county-nine implementation.

The coordinate was added to the fixed first seven research-question features. All features were standardized on the identical frozen cohort, and square roots of registered squared-distance budgets were applied: {BUDGET.tolist()}. Hazard receives1/12; population receives1/12; SOVI remains1/6. P2-to-eight comparison changes both feature presence and population budget allocation. A-to-CBM-to-NCV comparisons keep the H2 allocation identical. No clustering-performance-driven weights were selected.

The score does not incorporate actual resident/asset/loss/resilience adjustment in its operator; geography, hazard source assumptions and mixed event/event-day/probability factors still govern interpretation. It indicates relative geographic screening conditions, not literal hazard occurrence probability or modeled outage loss. Non-earthquake failures and compound restoration are not simulated. The five-policy MeanDelta and frozen social quartiles remain unchanged; Vulnerability-first's procedural use ofQ4 remains a potential RQ2/RQ3 dependence, not eliminated by using multiple policies. Cluster profiles are internal summaries, not independent validation. Proposed text is not inserted into the manuscript.
""")
    md('REPRODUCIBILITY.md',"""# Operations

Python3.12 registered Anaconda scientific stack; NumPy/pandas/GeoPandas/Shapely/PyMuPDF/scikit-learn/scipy/Matplotlib/threadpoolctl/requests. Exact package versions are in independent QA. Set LA_GRID_FROZEN_SOURCE_ROOT if the manifest-bound archive is elsewhere. source URLs/payload SHA/time and query parameters are archived; source files remain exact bytes (their registry carries the review label instead of altering originals).

From this diagnostic directory run, in order:

```powershell
python prepare.py
python acquire.py
python audit_sources.py
python information.py
python fit_candidates.py
python reports.py
python figures.py
python independent_qa.py
```

Acquisition reuses archived successful payloads. A clean clone needs GitLFS payloads and the original manifest-bound physical archive for full source-level provenance: neither prior1000-realization archives nor prior950 protected scientific files are newly republished by this package. Frozen copied comparator arrays allow conditionalfit reproduction without any new physical simulation. Some source-level authority checks require earlier packages and the exact base commit. Registered source failures remain failures; don't replacev1.19 with newer data. Windows long-path mode and common.lp are used for deep diagnostic paths.

Clustering preserves all204 registered fits and fitted labels. Source gates allow only the selected FEMA extension; Columbia14 is not fitted. Figures are diagnostics only. Independent QA checks source arithmetic, source hashes, geographic joins, standardized matrices, full-cohort silhouettes, inertia/labels, sensitivity metrics and950-file preservation. Publication PNGs are600dpi previews; rendered PDF review images are intermediate inspection records. No model, manuscript or formal result is changed.
""")
    print('Reports complete; bend K candidates',bends,'K4 LOO',k4.policy_LOO_cohort_min_ARI,'fixed',k4.policy_LOO_fixed_min_ARI,flush=True)


if __name__ == '__main__':
    main()
