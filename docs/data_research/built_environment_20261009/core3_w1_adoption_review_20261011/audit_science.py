"""Independently audit saved partitions, exact inputs and original-unit claims.
No fitting, label regeneration, PCA, GIS extraction or scientific stage execution.
"""
from common import *
import numpy as np,pandas as pd,itertools
from sklearn.metrics import adjusted_rand_score

def summaries(v):
    v=pd.to_numeric(pd.Series(v).dropna(),errors='raise').astype(float)
    return dict(mean=v.mean(),median=v.median(),p10=v.quantile(.1),p90=v.quantile(.9),zero_fraction=v.eq(0).mean(),valid_n=len(v))

def main():
    a=np.load(src(W+'CORE3_EXACT_INPUTS.npz'));ids=a['tract_ids'];values=a['values'];assert a['feature_columns'].tolist()==COLS
    archives={w:np.load(src(W+'run_records/'+w+'.npz')) for w in ['W1','W2','W3','W4','W5']}
    meta={w:json.loads(src(W+'run_records/'+w+'.json').read_text()) for w in archives}
    full=read('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv').set_index('tract_id')
    master=read(W+'CORE3_MASTER_2291.csv').set_index('tract_id');f=master.loc[ids].copy()
    old=read('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv').set_index('tract_id')
    rebuilt=full.loc[ids,COLS].copy()
    for c in COLS[:6]+['SOVI_SCORE','ALR_NPCTL']:rebuilt[c]=old.loc[ids,c]
    rebuilt['log1p_BUILDVALUE']=old.loc[ids,'log1p_NRI_BUILDVALUE']
    assert np.array_equal(rebuilt.to_numpy(),values)
    assert len(full)==2315 and len(master)==2291 and len(ids)==2287 and len(set(ids))==2287
    assert set(master.index)-set(ids)==set(UNRESOLVED) and not np.isnan(values).any()
    for i,c in enumerate(COLS):f[c]=values[:,i]
    ref=archives['W1'];y=ref['s42_labels'];fac=ref['coordinate_factors'];mean=ref['scaler_mean'];scale=ref['scaler_scale']
    assert np.array_equal(ref['tract_ids'],ids) and ref['feature_columns'].tolist()==COLS
    assert np.allclose(mean,values.mean(axis=0),atol=1e-12,rtol=1e-14) and np.allclose(scale,values.std(axis=0),atol=1e-12,rtol=1e-14)
    expected=np.array([np.sqrt(w/len(cols)) for w,cols in zip([.2,.2,.2,.2,.1,.1],DOMAINS.values()) for _ in cols])
    assert np.array_equal(fac,expected) and abs(np.square(fac).sum()-1)<1e-15
    z=(values-mean)/scale;x=z*fac
    matrix_hash=hashlib.sha256(x.tobytes()).hexdigest();assert matrix_hash==meta['W1']['signature']['weighted_matrix_sha256']
    idhash=hashlib.sha256('\n'.join(ids).encode()).hexdigest();assert idhash==meta['W1']['signature']['GEOID_order_sha256']
    centers=ref['s42_centers'];assert np.array_equal(np.square(x[:,None]-centers[None]).sum(axis=2).argmin(axis=1),y)
    assert np.bincount(y,minlength=4).tolist()==[650,802,801,34]
    np.savez_compressed(lp(OUT/'CORE3_W1_FROZEN_REFERENCE.npz'),tract_ids=ids,feature_columns=np.array(COLS),values=values,scaler_mean=mean,scaler_scale=scale,coordinate_factors=fac,weighted_matrix=x,labels=y,fitted_centers=centers)
    labels=master.reset_index()[['tract_id','formal_population']].copy();labeldict=dict(zip(ids,y));labels['source_raw_class']=labels.tract_id.map(labeldict).astype('Int64');labels['review_class']=labels.source_raw_class.map(lambda v:'C'+str(int(v)+1) if pd.notna(v) else None);labels['classification_status']=np.where(labels.review_class.notna(),'CLASSIFIED','UNCLASSIFIED_GEOMETRY');save('CORE3_W1_LABELS_2291.csv',labels)
    units=['h','fraction','mapped graph degree','mapped lambda2 impact','mapped graph betweenness','dependency concentration HHI','built area / valid tract land','housing units in 5+ structures / all units','normalized classified-land entropy','published social vulnerability score','natural log1p of archived building-value dollars','national composite loss-rate percentile']
    profile=[];wide=[]
    coverage=['scag2020_classified_land_coverage','jrc_total_valid_land_coverage','housing_5plus_share_moe90','housing_5plus_share_boundary_model']
    coverage=[c for c in coverage if c in full];extra=['NRI_BUILDVALUE','T80']+coverage
    for k in range(4):
        mask=y==k;d=f.loc[mask];r=dict(review_class='C'+str(k+1),source_raw_class=k,n=int(mask.sum()),tract_share=mask.mean(),mapped_population=d.formal_population.sum(),population_share=d.formal_population.sum()/f.formal_population.sum());base=r.copy()
        for c,u in zip(COLS+extra,units+['archived source dollars','h']+['fraction' if 'coverage' in c else 'survey quality diagnostic' for c in coverage]):
            v=d[c] if c in d else full.loc[d.index,c];ss=summaries(v)
            profile.append(dict(**base,feature=c,units=u,statistical_weight='unweighted tract',**ss))
            r[c+'_mean']=ss['mean'];r[c+'_median']=ss['median']
        r['population_weighted_service_loss_hr']=np.average(d.B_480_hr,weights=d.formal_population);wide.append(r)
    save('CORE3_W1_VERIFIED_PROFILES.csv',profile);save('CORE3_W1_PROFILE_TABLE.csv',wide)
    save('UNCLASSIFIED_RESIDENTIAL_TRACTS.csv',full.loc[UNRESOLVED,['formal_population','B_480_hr','T80','Init_Supply','SOVI_SCORE','housing_5plus_share']].reset_index())
    outside=full.loc[~full.index.isin(master.index)];assert len(outside)==24
    save('OUTSIDE_RESIDENTIAL_COHORT.csv',outside[['formal_population','housing_total']].reset_index())
    # Three scientific versions: exact common-GEOID cells, no ID equivalence assumed.
    formal=pd.read_csv(source('Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv',commit='031d2c675f8e7d58035d27448be040b809ced086'),dtype={'tract_id':str})
    original_lengths=formal.tract_id.str.len().value_counts().to_dict()
    formal['tract_id']=formal.tract_id.str.zfill(11)
    assert formal.tract_id.str.fullmatch(r'\d{11}').all() and formal.tract_id.is_unique
    dump('FORMAL_GEOID_SERIALIZATION_AUDIT.json',dict(original_character_lengths=original_lengths,canonicalization='Restore leading zero to archived numeric GEOID serialization; exact match to 11-character Census universe',records=len(formal),source_file_not_modified=True))
    formal=formal.set_index('tract_id')
    b=read(B+'STAGE7_CANDIDATE_LABELS_2291.csv').set_index('tract_id');assert set(formal.index)==set(master.index)==set(b.index)
    bparams=np.load(src(B+'STAGE7_CANDIDATE_PARAMETERS.npz'));bids=bparams['tract_id'];bl=bparams['labels'];assert np.bincount(bl).tolist()==[850,34,651,752]
    assert np.array_equal(b.loc[bids,'source_raw_cluster'].astype(int).to_numpy(),bl)
    bhash=json.loads(src(B+'STAGE7_CANDIDATE_FREEZE.json').read_text());assert hashlib.sha256(bl.tobytes()).hexdigest()==bhash['original_saved_label_sha256']
    joined=pd.DataFrame({'tract_id':ids,'A_formal_class':formal.loc[ids,'cluster'].to_numpy(),'B_BE0_raw_class':b.loc[ids,'source_raw_cluster'].astype(int).to_numpy(),'B_BE0_display_class':b.loc[ids,'candidate_cluster'].to_numpy(),'C_CORE3_raw_class':y,'C_CORE3_review_class':['C'+str(int(k)+1) for k in y]})
    save('STAGE7_TRACT_VERSION_MEMBERSHIP.csv',joined)
    transitions=[];versionqa={};alignment=[]
    for av,bv,ca,cb in [('A_FORMAL5','B_BE0_4','A_formal_class','B_BE0_raw_class'),('A_FORMAL5','C_CORE3_W1_4','A_formal_class','C_CORE3_raw_class'),('B_BE0_4','C_CORE3_W1_4','B_BE0_raw_class','C_CORE3_raw_class')]:
        tab=pd.crosstab(joined[ca],joined[cb]);versionqa[av+'__'+bv]={'N':len(joined),'ARI':adjusted_rand_score(joined[ca],joined[cb])}
        from scipy.optimize import linear_sum_assignment
        ii,jj=linear_sum_assignment(-tab.to_numpy());mapping={int(tab.columns[j]):int(tab.index[i]) for i,j in zip(ii,jj)}
        for i,j in itertools.product(tab.index,tab.columns):transitions.append(dict(source_version=av,target_version=bv,source_class=int(i),target_class=int(j),n=int(tab.loc[i,j]),fraction_of_source=float(tab.loc[i,j]/tab.loc[i].sum()),fraction_of_target=float(tab.loc[i,j]/tab[j].sum()),common_GEOID_n=len(joined),comparison_only_target_match_to_source=mapping.get(int(j)),scientific_equivalence=False))
        for i,j in zip(ii,jj):alignment.append(dict(source_version=av,target_version=bv,source_class=int(tab.index[i]),target_class=int(tab.columns[j]),overlap=int(tab.iloc[i,j]),purpose='Comparison display only; unequal class counts leave an unmatched source class',scientific_equivalence=False))
    save('STAGE7_VERSION_CROSSWALK.csv',transitions);save('STAGE7_COMPARISON_ID_ALIGNMENT.csv',alignment);dump('STAGE7_VERSION_COMPARISON_QA.json',versionqa)
    historyprofiles=[]
    for version,frame0,labelcol in [('A_FORMAL5',formal.loc[ids],'cluster'),('B_BE0_4',old.loc[ids].assign(class_id=joined.B_BE0_raw_class.to_numpy()),'class_id'),('C_CORE3_W1_4',f.assign(class_id=y),'class_id')]:
        for k,d in frame0.groupby(labelcol):
            for c in ['T80','B_480_hr','Init_Supply','SOVI_SCORE','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','Pre_1970_Ratio','Pop_Density','NRI_BUILDVALUE','NRI_RISK_SCORE','ALR_NPCTL','land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share',*COLS[6:9]]:
                if c in d:historyprofiles.append(dict(version=version,class_id=int(k),feature=c,common_sample_n=len(ids),**summaries(d[c])))
    save('STAGE7_HISTORICAL_ORIGINAL_UNIT_PROFILES.csv',historyprofiles)
    # Saved-run validation, seed pairs, spatial tables, raw contingency and variance.
    seedpair=[];spatial=[];weight=[];domain=[];rawcts=[];partitions={};minor=[];minorprofiles=[];members=[];profilechanges=[]
    registered=read(W+'CORE3_WEIGHT_SPATIAL_STABILITY.csv').set_index(['scheme','seed'])
    targetids=json.loads(src(R+'D34_REFERENCE_IDENTITY.json').read_text())['tract_ids'];target=np.isin(ids,targetids);assert target.sum()==34 and np.array_equal(target,y==3)
    baseprofiles=np.stack([values[y==k].mean(axis=0) for k in range(4)])
    for w,arc in archives.items():
        assert np.array_equal(arc['tract_ids'],ids)
        for aa,bb in itertools.combinations(SEEDS,2):seedpair.append(dict(scheme=w,seed_a=aa,seed_b=bb,ARI=adjusted_rand_score(arc[f's{aa}_labels'],arc[f's{bb}_labels'])))
        for seed in SEEDS:
            own=arc[f's{seed}_labels'];train=arc[f's{seed}_train_mask'];pred=arc[f's{seed}_spatial_prediction'];ones=np.ones(len(y),bool)
            own_display,dispmap,_=match(y,own,ones)
            # Spatial matching ONLY retained training; display map inherited from full fit.
            mapped,spmap,ct=match(own,pred,train);display_spatial=np.array([dispmap[int(t)] for t in mapped])
            partitions.setdefault(w+'_full',[]).append((seed,own_display));partitions.setdefault(w+'_spatial',[]).append((seed,display_spatial))
            for scope,mask in [('all',ones),('training',train),('heldout',~train)]:
                t=np.zeros((4,4),int);np.add.at(t,(own[mask],pred[mask]),1)
                for i,j in itertools.product(range(4),repeat=2):rawcts.append(dict(scheme=w,seed=seed,scope=scope,own_full_raw_class=i,perturbed_raw_class=j,n=int(t[i,j]),training_selected_map_to_own_full=spmap[j]))
            import ast
            deleted=sorted(np.unique(a['block_ids'][~train]).tolist())
            assert deleted==sorted(ast.literal_eval(registered.loc[(w,seed),'removed_blocks']))
            spatial.append(dict(scheme=w,seed=seed,train_n=int(train.sum()),heldout_n=int((~train).sum()),removed_blocks=json.dumps(deleted),ARI_all=adjusted_rand_score(own,pred),ARI_training=adjusted_rand_score(own[train],pred[train]),ARI_heldout=adjusted_rand_score(own[~train],pred[~train]),reassigned_n=int((own!=mapped).sum())))
            for k in range(4):
                baseline=(own==k);support=int((baseline&train).sum())
                for scope,mask in [('all',ones),('training',train),('heldout',~train)]:
                    bm=baseline&mask;pm=(mapped==k)&mask;inter=int((bm&pm).sum());union=int((bm|pm).sum())
                    outcounts=np.bincount(mapped[bm&~pm],minlength=4);incounts=np.bincount(own[pm&~bm],minlength=4)
                    members.append(dict(scheme=w,seed=seed,scope=scope,own_full_raw_class=k,W1_reference_display_class='C'+str(dispmap[k]+1),baseline_n=int(bm.sum()),training_support=support,prediction_n=int(pm.sum()),intersection=inter,union=union,retention=inter/bm.sum() if bm.sum() else None,purity=inter/pm.sum() if pm.sum() else None,Jaccard=inter/union if union else None,incoming=int((pm&~bm).sum()),outgoing=int((bm&~pm).sum()),outgoing_destination_counts=json.dumps(outcounts.tolist()),incoming_origin_counts=json.dumps(incounts.tolist()),training_supported=bool(support)))
                    for h,c in enumerate(COLS):
                        baseline_full_mean=values[baseline,h].mean();fixed=values[bm,h];changed=values[pm,h]
                        profilechanges.append(dict(scheme=w,seed=seed,scope=scope,own_full_raw_class=k,W1_reference_display_class='C'+str(dispmap[k]+1),feature=c,baseline_full_n=int(baseline.sum()),fixed_members_n=len(fixed),matched_members_n=len(changed),baseline_full_mean=baseline_full_mean,fixed_members_mean=fixed.mean() if len(fixed) else None,matched_prediction_mean=changed.mean() if len(changed) else None,matched_prediction_median=np.median(changed) if len(changed) else None,sample_deletion_change=fixed.mean()-baseline_full_mean if len(fixed) else None,membership_replacement_change=changed.mean()-fixed.mean() if len(fixed) and len(changed) else None,standardized_total_center_change=(changed.mean()-baseline_full_mean)/scale[h] if len(changed) else None))
            against=archives['W1'][f's{seed}_labels'];aligned,_,_=match(against,own,ones)
            weight.append(dict(scheme=w,seed=seed,ARI_vs_same_seed_W1=adjusted_rand_score(against,own),reassigned_n=int((against!=aligned).sum()),reassigned_percentage=100*(against!=aligned).mean()))
            xx=z*arc['coordinate_factors'];overall=xx.mean(axis=0);tss=np.square(xx-overall).sum(axis=0);bss=sum((own==k).sum()*np.square(xx[own==k].mean(axis=0)-overall) for k in range(4));wss=sum(np.square(xx[own==k]-xx[own==k].mean(axis=0)).sum(axis=0) for k in range(4));assert np.allclose(tss,bss+wss,atol=1e-9,rtol=1e-12)
            for dom,cols in DOMAINS.items():
                ii=[COLS.index(c) for c in cols];domain.append(dict(scheme=w,seed=seed,domain=dom,nominal_squared_weight=np.square(arc['coordinate_factors'][ii]).sum(),TSS=tss[ii].sum(),BSS=bss[ii].sum(),WSS=wss[ii].sum(),domain_between_fraction=bss[ii].sum()/bss.sum(),domain_explained_fraction=bss[ii].sum()/tss[ii].sum()))
            dominant=int(np.bincount(own[target],minlength=4).argmax())
            for scope,labels0,mask in [('full_fit',own,ones),('spatial_all',mapped,ones),('spatial_training',mapped,train),('spatial_heldout',mapped,~train)]:
                tg=target&mask;pm=(labels0==dominant)&mask;inter=int((tg&pm).sum());union=int((tg|pm).sum());counts=np.bincount(labels0[tg],minlength=4);largest=int(counts.argmax())
                support=int(target.sum()) if scope=='full_fit' else int((target&train).sum())
                basis='largest original-member overlap in saved full partition; comparison only' if scope=='full_fit' else 'training overlap only; zero matched retention does not mean tracts disappear'
                row=dict(scheme=w,seed=seed,scope=scope,reference_n=int(tg.sum()),training_support=support,own_full_target_class=dominant,matched_prediction_n=int(pm.sum()),original_members_retained=inter,incoming_nonreference_members=int((pm&~target).sum()),retention=inter/tg.sum() if tg.sum() else np.nan,purity=inter/pm.sum() if pm.sum() else np.nan,Jaccard=inter/union if union else np.nan,destination_counts=json.dumps(counts.tolist()),number_of_destination_classes=int((counts>0).sum()),largest_destination_original_members=int(counts[largest]),largest_destination_total_n=int(((labels0==largest)&mask).sum()),training_supported=bool(support),matching_basis=basis)
                minor.append(row)
                for c in COLS:
                    fixed=values[tg,COLS.index(c)];changed=values[pm,COLS.index(c)]
                    minorprofiles.append(dict(scheme=w,seed=seed,scope=scope,feature=c,fixed_original_members_mean=fixed.mean() if len(fixed) else None,matched_group_mean=changed.mean() if len(changed) else None,reference_full_34_mean=values[target,COLS.index(c)].mean(),reference_observed_n=len(fixed),matched_observed_n=len(changed)))
    save('VERIFIED_SEED_PAIR_ARI.csv',seedpair);save('VERIFIED_SPATIAL_RUNS.csv',spatial);save('VERIFIED_WEIGHT_REASSIGNMENTS.csv',weight);save('VERIFIED_DOMAIN_SEPARATION.csv',domain);save('VERIFIED_SPATIAL_RAW_CONTINGENCIES.csv',rawcts);save('CORE3_W1_MINOR_GROUP_AUDIT.csv',minor);save('MINOR_GROUP_ORIGINAL_UNIT_PROFILE_CHANGES.csv',minorprofiles)
    save('CLASS_MEMBERSHIP_STABILITY.csv',members);save('CORE3_PROFILE_PERTURBATIONS.csv',profilechanges)
    # Exact denominators of profile-direction support, using saved partitions only.
    claims=[];casevalues=[]
    for i,j in itertools.combinations(range(4),2):
        for h,c in enumerate(COLS):
            refdiff=baseprofiles[i,h]-baseprofiles[j,h];refsign=np.sign(refdiff)
            for family,pp in partitions.items():
                deltas=[]
                for seed,labels0 in pp:
                    delta=values[labels0==i,h].mean()-values[labels0==j,h].mean();deltas.append(delta)
                    casevalues.append(dict(class_a='C'+str(i+1),class_b='C'+str(j+1),feature=c,comparison_family=family,seed=seed,reference_mean_difference=refdiff,case_mean_difference=delta,supports_reference_direction=bool(np.sign(delta)==refsign),reverses_reference_direction=bool(np.sign(delta)==-refsign)))
                ds=np.array(deltas);sg=np.sign(ds);claims.append(dict(class_a='C'+str(i+1),class_b='C'+str(j+1),feature=c,reference_mean_a=baseprofiles[i,h],reference_mean_b=baseprofiles[j,h],reference_mean_difference=refdiff,comparison_family=family,N=len(ds),supporting_cases=int((sg==refsign).sum()),contradicting_cases=int((sg==-refsign).sum()),exact_zero_cases=int((sg==0).sum()),difference_median=np.median(ds),difference_min=ds.min(),difference_max=ds.max(),interpretation='Direction of tract-mean difference, not significance, magnitude equivalence or independent geographic validation'))
    save('CORE3_W1_CLAIM_STABILITY.csv',claims);save('CLAIM_STABILITY_CASE_VALUES.csv',casevalues)
    sp=pd.DataFrame(spatial);pairs=pd.DataFrame(seedpair);ww=pd.DataFrame(weight);dd=pd.DataFrame(domain);mm=pd.DataFrame(minor)
    observed={}
    for w in archives:
        ps=pairs.loc[pairs.scheme.eq(w),'ARI'];ss=sp.loc[sp.scheme.eq(w)];ws=ww.loc[ww.scheme.eq(w)];observed[w]={'seed_pair_ARI_median':ps.median(),'seed_pair_ARI_min':ps.min(),'spatial_ARI_median':ss.ARI_all.median(),'spatial_ARI_min':ss.ARI_all.min(),'spatial_ARI_p05':ss.ARI_all.quantile(.05),'spatial_reassignment_max':ss.reassigned_n.max(),'weight_reassignment_percent_median':ws.reassigned_percentage.median()}
    published=read(W+'CORE3_WEIGHT_COMPARISONS.csv').set_index('scheme')
    for w,v in observed.items():
        for new,oldkey in [('seed_pair_ARI_median','seed_pair_ARI_median'),('seed_pair_ARI_min','seed_pair_ARI_min'),('spatial_ARI_median','spatial_ARI_median'),('spatial_ARI_min','spatial_ARI_min'),('spatial_reassignment_max','spatial_changed_n_max')]:assert np.isclose(v[new],published.loc[w,oldkey],atol=1e-12)
        assert np.isclose(v['weight_reassignment_percent_median']/100,published.loc[w,'reassigned_fraction_median'],atol=1e-12)
    adverse=mm.loc[mm.scheme.eq('W1')&mm.seed.eq(54)&mm.scope.eq('spatial_all')].iloc[0];assert adverse.original_members_retained==34 and adverse.matched_prediction_n==92 and np.isclose(adverse.purity,34/92)
    dump('INDEPENDENT_SCIENTIFIC_QA.json',dict(authoritative_commit=BASELINE,exact_source_reconstruction=True,primary_n=2287,master_n=2291,full_domain_n=2315,unclassified=UNRESOLVED,full_population=full.formal_population.sum(),classified_population=f.formal_population.sum(),unclassified_population=full.loc[UNRESOLVED].formal_population.sum(),outside_cohort_population=outside.formal_population.sum(),weighted_matrix_sha256=matrix_hash,GEOID_order_sha256=idhash,exact_saved_estimator_centers=True,saved_labels_hash=hashlib.sha256(y.tobytes()).hexdigest(),saved_centers_hash=hashlib.sha256(centers.tobytes()).hexdigest(),coordinate_budget_sum=np.square(fac).sum(),schemes=observed,W1_domain_between_fraction_median=dd.loc[dd.scheme.eq('W1')].groupby('domain').domain_between_fraction.median().to_dict(),minority_reference_members=targetids,new_fits=0,new_PCA=0,new_k_searches=0,new_physical_or_GA_runs=0,adoption_decision='ADOPT_AS_CONDITIONAL_STAGE7_REFERENCE',formal_promotion=False))
    text('REFERENCE_ID_CONVENTION.md','C1 = frozen raw class 0 (650 tracts); C2 = raw 1 (802); C3 = raw 2 (801); C4 = raw 3 (34). These are new package identifiers only. Historical formal/BE0 IDs are separately retained in STAGE7_TRACT_VERSION_MEMBERSHIP.csv and the contingency tables; overlap matching does not establish scientific equivalence.')
    log('Independent source reconstruction, saved-center predictions, version crosswalks, 950 seed-pair ARIs, 100 spatial cases, all 12-coordinate claim directions and minority specificity verified without fitting.')
if __name__=='__main__':main()
