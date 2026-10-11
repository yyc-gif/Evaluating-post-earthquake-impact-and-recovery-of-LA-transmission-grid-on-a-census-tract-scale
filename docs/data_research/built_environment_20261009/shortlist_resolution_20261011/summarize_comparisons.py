"""Summaries, source-error predictions and 20 predeclared coverage fits."""
from common import *
from controlled_shortlist import MODELS,SEEDS,PARAMS,domains,design,align,prepare
import numpy as np,pandas as pd,itertools,time
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

PROFILE=['B_480_hr','T80','Init_Supply','SOVI_SCORE','emc2022_total_built_land_fraction','building_footprint_coverage','housing_5plus_share','housing_detached_share','scag2020_classified_land_entropy','land_use_entropy','scag2020_classified_land_coverage','land_use_classified_land_coverage','assessor2022_actual_pre1970_main_area_share','assessor2022_actual_age_main_area_coverage','all_use2014_pre1970_area_share','all_use2014_age_coverage','acs_residential_pre1970_share','nlcd_c12_2022_impervious_fraction','outline_height_area_weighted_centroid_m','outline_valid_height_area_fraction_centroid','log1p_BUILDVALUE','NRI_BUILDVALUE','ALR_NPCTL','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']

def metrics(g):
    return dict(mean=g.mean(),median=g.median(),p10=g.quantile(.1),p90=g.quantile(.9),zero_fraction=g.eq(0).sum()/g.notna().sum() if g.notna().any() else None,valid_n=int(g.notna().sum()))

def summarize():
    f,blocks,cases,spec=prepare();allmeta=[];data={};models={};fullprofiles=[];seedstability=[];matchrows=[];crossrows=[];spprofiles=[];revrows=[];contributions=[];small=[];predict=[]
    for name,phys in MODELS.items():
        z=np.load(lp(OUT/'run_records'/(name+'.npz')));data[name]=z;meta=json.loads(lp(OUT/'run_records'/(name+'.json')).read_text(encoding='utf-8'));assert meta['completed_seeds']==SEEDS;allmeta+=meta['rows'];models[name]=f.loc[z['tract_ids']].copy()
    hist=data['HIST'];h42=hist['s42_labels'];cid=int(np.argmin(np.bincount(h42)));target=set(hist['tract_ids'][h42==cid]);assert len(target)==34
    dump('D34_REFERENCE_IDENTITY.json',dict(model='HIST (saved D equal-five-domains)',seed=42,label_zero_based=cid,tract_ids=sorted(target),target_n=34,not_forced_to_be_a_cluster_in_other_models=True))
    for name,z in data.items():
        d=models[name];dom=domains(MODELS[name]);cols=z['feature_columns'].tolist();factors=z['coordinate_factors'];labs42=z['s42_labels'];x=(d[cols].to_numpy()-z['scaler_mean'])/z['scaler_scale']*factors
        for a,b in itertools.combinations(SEEDS,2):seedstability.append(dict(model=name,seed_a=a,seed_b=b,ARI=adjusted_rand_score(z[f's{a}_labels'],z[f's{b}_labels']),n=len(d)))
        between=[]
        for i,c in enumerate(cols):
            v=x[:,i];ss=sum((labs42==k).sum()*(v[labs42==k].mean()-v.mean())**2 for k in range(4));between.append(ss)
        for domain,fields in dom.items():
            for c in fields:
                i=cols.index(c);contributions.append(dict(model=name,domain=domain,feature=c,n=len(d),domain_squared_distance_budget=.2,coordinate_squared_distance_weight=factors[i]**2,coordinate_factor=factors[i],total_weighted_sum_squares=np.square(x[:,i]-x[:,i].mean()).sum(),between_cluster_sum_squares=between[i],share_of_total_between_cluster_sum_squares=between[i]/sum(between),meaning='coordinate contribution to descriptive separation, not causal effect or physical feature quality'))
        for seed in SEEDS:
            labels=z[f's{seed}_labels'];pred=z[f's{seed}_spatial_prediction'];train=z[f's{seed}_train_mask'];mapped,tab,mp=align(labels,pred,train);display,_,ownmap=align(labs42,labels,np.ones(len(d),bool))
            aligneddisplay=np.array([ownmap[k] for k in mapped]);tm=d.index.isin(target)
            # D34 diagnostic: the baseline class with greatest D34 overlap in this model.
            target_class=max(range(4),key=lambda k:int(((labels==k)&tm).sum()));j=np.flatnonzero((mapped==target_class)&tm).size;pn=(mapped==target_class).sum()
            small.append(dict(model=name,seed=seed,target_original_n=int(tm.sum()),target_training_n=int((tm&train).sum()),own_baseline_smallest_class_n=int(np.bincount(labels).min()),D34_overlap_in_baseline_selected_class=int(((labels==target_class)&tm).sum()),matched_prediction_n=int(pn),D34_retained_n=int(j),D34_retention=j/tm.sum(),D34_purity=j/pn if pn else None,no_target_training_support=not (tm&train).any(),removed_blocks=';'.join(cases[seed])))
            for scope,mask in [('full',np.ones(len(d),bool)),('training',train),('heldout',~train)]:
                rawtab=np.zeros((4,4),int)
                for aa,bb in zip(labels[mask],pred[mask]):rawtab[aa,bb]+=1
                for aa,bb in itertools.product(range(4),repeat=2):crossrows.append(dict(model=name,seed=seed,scope=scope,baseline_raw_class=int(aa),prediction_raw_class=int(bb),n=int(rawtab[aa,bb]),training_selected_prediction_maps_to=int(mp[bb])))
                for k in range(4):
                    original=(labels==k)&mask;prediction=(mapped==k)&mask;intersection=int((original&prediction).sum());union=int((original|prediction).sum());bn=int(original.sum());pn=int(prediction.sum());outflow=pd.Series(mapped[original &~prediction]).value_counts();inflow=pd.Series(labels[prediction &~original]).value_counts()
                    matchrows.append(dict(model=name,seed=seed,scope=scope,baseline_class=k,display_seed42_class=int(ownmap[k]),baseline_n=bn,training_baseline_n=int(((labels==k)&train).sum()),predicted_n=pn,intersection=intersection,union=union,retention=intersection/bn if bn else None,purity=intersection/pn if pn else None,Jaccard=intersection/union if union else None,training_support='PRESENT' if ((labels==k)&train).any() else 'NO_TRAINING_SUPPORT',major_outflow_class=int(outflow.index[0]) if len(outflow) else None,major_outflow_n=int(outflow.iloc[0]) if len(outflow) else 0,major_inflow_class=int(inflow.index[0]) if len(inflow) else None,major_inflow_n=int(inflow.iloc[0]) if len(inflow) else 0,no_training_support_matching_not_substantively_identified=not ((labels==k)&train).any()))
            for k in range(4):
                bm=labels==k;pm=mapped==k;retained=bm&train
                for c in PROFILE:
                    basevalue=d.loc[bm,c];basemean=basevalue.mean();s=d[c].std()
                    if seed==42:fullprofiles.append(dict(model=name,display_class=k,n=int(bm.sum()),tract_share=bm.mean(),population=float(d.loc[bm,'formal_population'].sum()),population_share=d.loc[bm,'formal_population'].sum()/d.formal_population.sum(),feature=c,statistic_weight='unweighted tracts',**metrics(basevalue)))
                    for pop,mask in [('fixed_baseline_members_retained',retained),('reclustered_matched_full',pm)]:
                        v=d.loc[mask,c];spprofiles.append(dict(model=name,seed=seed,baseline_class=k,display_seed42_class=int(ownmap[k]),profile_population=pop,feature=c,n=int(mask.sum()),baseline_mean=basemean,mean_change_raw_units=v.mean()-basemean,mean_change_standardized=(v.mean()-basemean)/s if s else None,**metrics(v)))
            for a,b in itertools.combinations(range(4),2):
                for c in PROFILE:
                    delta=d.loc[labels==a,c].mean()-d.loc[labels==b,c].mean();post=d.loc[mapped==a,c].mean()-d.loc[mapped==b,c].mean();sd=d[c].std();revrows.append(dict(model=name,seed=seed,display_class_a=int(ownmap[a]),display_class_b=int(ownmap[b]),feature=c,baseline_difference=delta,post_difference=post,baseline_difference_standardized=delta/sd if sd else None,direction_reversed=bool(delta*post<0)))
            predict.append(pd.DataFrame({'model':name,'seed':seed,'tract_id':d.index,'training':train,'full_raw_class':labels,'spatial_raw_class':pred,'spatial_aligned_own_seed_class':mapped,'display_full_seed42_class':display,'display_spatial_seed42_class':aligneddisplay,'changed':mapped!=labels}))
    save('FULL_SEED_STABILITY.csv',seedstability);save('CLUSTER_PROFILE_VALUES.csv',fullprofiles);save('SPATIAL_CLUSTER_MATCHING.csv',matchrows);save('SPATIAL_RAW_CONTINGENCIES.csv',crossrows);save('SPATIAL_PROFILE_STABILITY.csv',spprofiles);save('PROFILE_DIRECTION_REVERSALS.csv',revrows);save('DOMAIN_COORDINATE_CONTRIBUTIONS.csv',contributions);save('MINORITY_CLASS_STABILITY.csv',small);save('TRACT_PREDICTIONS.csv',pd.concat(predict,ignore_index=True))
    pairrows=[];cont=[]
    for a,b in itertools.combinations(MODELS,2):
        za,zb=data[a],data[b];ia=pd.Index(za['tract_ids']);ib=pd.Index(zb['tract_ids']);common=ia.intersection(ib,sort=False);pa=ia.get_indexer(common);pb=ib.get_indexer(common)
        for seed in SEEDS:
            la=za[f's{seed}_labels'][pa];lb=zb[f's{seed}_labels'][pb];aligned,_,mapping=align(la,lb,np.ones(len(la),bool));pairrows.append(dict(model_a=a,model_b=b,seed=seed,n=len(common),ARI=adjusted_rand_score(la,lb),reassigned_n=int((la!=aligned).sum()),reassigned_fraction=(la!=aligned).mean(),same_training_cohort=ia.equals(ib),not_pure_measurement_effect_if_samples_differ=not ia.equals(ib),GEOID_order_sha256=hashlib.sha256('\n'.join(common).encode()).hexdigest()))
            tab=np.zeros((4,4),int)
            for x,y in zip(la,lb):tab[x,y]+=1
            for x,y in itertools.product(range(4),repeat=2):cont.append(dict(model_a=a,model_b=b,seed=seed,class_a=x,class_b_raw=y,class_b_aligned_to_a=int(mapping[y]),n=int(tab[x,y]),row_fraction=tab[x,y]/tab[x].sum() if tab[x].sum() else None))
    save('BETWEEN_MODEL_COMPARISONS.csv',pairrows);save('BETWEEN_MODEL_CONTINGENCIES.csv',cont)
    runs=pd.DataFrame(allmeta);seeddf=pd.DataFrame(seedstability);sm=pd.DataFrame(small);sp=pd.DataFrame(matchrows);summary=[]
    for name,g in runs.groupby('model',sort=False):
        ari=seeddf.loc[seeddf.model.eq(name),'ARI'];v=sm.loc[sm.model.eq(name)];cl=sp.loc[sp.model.eq(name)&sp.scope.eq('full')];summary.append(dict(model=name,physical_coordinates=';'.join(MODELS[name]),cohort_n=int(g.cohort_n.iloc[0]),full_seed_pair_ARI_median=ari.median(),full_seed_pair_ARI_min=ari.min(),spatial_ARI_median=g.full_ARI.median(),spatial_ARI_p05=g.full_ARI.quantile(.05),spatial_ARI_min=g.full_ARI.min(),training_ARI_median=g.training_ARI.median(),heldout_ARI_median=g.heldout_ARI.median(),silhouette_mean=g.silhouette.mean(),minimum_full_class_n=g.minimum_class_n.min(),reassigned_n_median=g.aligned_reassigned_n.median(),reassigned_n_max=g.aligned_reassigned_n.max(),class_Jaccard_min=cl.Jaccard.min(),D34_retention_min=v.D34_retention.min(),D34_purity_min=v.D34_purity.min(),D34_prediction_n_max=v.matched_prediction_n.max(),worst_spatial_seed=int(g.loc[g.full_ARI.idxmin(),'seed']),worst_removed_blocks=g.loc[g.full_ARI.idxmin(),'removed_blocks'],fit_records=40,role='historical reference' if name=='HIST' else 'conditional extension' if name in ['CORE4','AGE_HIST','HEIGHT_HIST_EXT'] else 'bounded comparison',metrics_not_feature_admission_criteria=True))
    save('BOUNDED_MODEL_COMPARISON.csv',summary)
    rev=pd.DataFrame(revrows);rev['display_low']=rev[['display_class_a','display_class_b']].min(axis=1);rev['display_high']=rev[['display_class_a','display_class_b']].max(axis=1)
    save('PROFILE_DIRECTION_REVERSAL_SUMMARY.csv',rev.groupby(['model','display_low','display_high','feature']).agg(perturbations=('direction_reversed','size'),reversals=('direction_reversed','sum'),baseline_absolute_standardized_difference_min=('baseline_difference_standardized',lambda x:x.abs().min())).reset_index())
    log('Partition, class retention/purity, original-unit profiles and all pairwise contingencies summarized.')
    return f,data,models

def uncertainty_and_coverage(f,data,models):
    name='CORE3';z=data[name];d=models[name];cols=z['feature_columns'].tolist();factors=z['coordinate_factors'];labels=z['s42_labels'];centers=z['s42_centers'];reps=np.load(lp(OUT/'ACS_CONFIGURATION_REPLICATES.npz'));assert np.array_equal(reps['tract_ids'],d.index)
    x=(d[cols].to_numpy()-z['scaler_mean'])/z['scaler_scale']*factors;ci=cols.index('housing_5plus_share');rows=[]
    for r in range(80):
        xx=x.copy();xx[:,ci]=(reps['housing_5plus_share'][:,r]-z['scaler_mean'][ci])/z['scaler_scale'][ci]*factors[ci];pred=np.square(xx[:,None,:]-centers[None,:,:]).sum(axis=2).argmin(axis=1)
        rows.append(dict(replicate=r+1,n=len(d),changed_n=int((pred!=labels).sum()),ARI=adjusted_rand_score(labels,pred),model_refit=False,meaning='fixed-centroid response to survey replicate coordinates, not refitted cluster uncertainty'))
    save('ACS_FIXED_MODEL_MEASUREMENT_SENSITIVITY.csv',rows)
    # Full-cohort predictions after a prespecified continuous-support restriction.
    threshold=d.scag2020_classified_land_coverage.quantile(.25);train=d.scag2020_classified_land_coverage.ge(threshold).to_numpy();folder=lp(OUT/'run_records');p=folder/'CORE3_coverage.npz';meta=p.with_suffix('.json');record=[];saved={'tract_ids':d.index.to_numpy(dtype='U11'),'train_mask':train,'feature_columns':np.array(cols,dtype='U64'),'coordinate_factors':factors}
    if p.exists() and meta.exists():
        record=json.loads(meta.read_text(encoding='utf-8'))['rows'];zz=np.load(p);assert np.array_equal(zz['tract_ids'],d.index) and np.array_equal(zz['train_mask'],train);saved={k:zz[k] for k in zz.files}
    with threadpool_limits(limits=1):
        for seed in SEEDS:
            if any(r['seed']==seed for r in record):continue
            xx,_,_,sc=design(d,MODELS[name],train);km=KMeans(**PARAMS,random_state=seed).fit(xx[train]);pred=km.predict(xx);base=z[f's{seed}_labels'];mapped,_,_=align(base,pred,train)
            record.append(dict(seed=seed,training_n=int(train.sum()),heldout_low_coverage_n=int((~train).sum()),classified_coverage_quartile_cutoff=threshold,full_ARI=adjusted_rand_score(base,pred),training_ARI=adjusted_rand_score(base[train],pred[train]),heldout_ARI=adjusted_rand_score(base[~train],pred[~train]),changed_n=int((base!=mapped).sum()),inertia=km.inertia_,iterations=km.n_iter_,criterion='bottom coverage quartile excluded as declared diagnostic, not measurement admission rule'))
            saved[f's{seed}_prediction']=pred;saved[f's{seed}_mean']=sc.mean_;saved[f's{seed}_scale']=sc.scale_;saved[f's{seed}_centers']=km.cluster_centers_;np.savez_compressed(p,**saved);meta.write_text(json.dumps(clean({'rows':record}),indent=2)+'\n',encoding='utf-8')
    save('COVERAGE_SAMPLE_SENSITIVITY.csv',record)
    rows=[]
    for group,mask in [('high_coverage_training',train),('low_coverage_heldout',~train)]:
        for c in PROFILE:rows.append(dict(group=group,n=int(mask.sum()),feature=c,**metrics(d.loc[mask,c])))
    save('COVERAGE_EXCLUDED_COHORT_PROFILES.csv',rows);save('COVERAGE_EXCLUDED_GEOIDS.csv',pd.DataFrame({'tract_id':d.index[~train],'scag2020_classified_land_coverage':d.loc[~train,'scag2020_classified_land_coverage']}))
    dump('COMPARISON_COMPLETION_QA.json',dict(predeclared_models=len(MODELS),new_full_fits=220,new_spatial_fits=220,new_coverage_fits=20,reused_full=20,reused_spatial=20,total_new_fits=460,new_k_searches=0,measurement_replicate_predictions=80,physical_samples_generated=0,formal_scientific_files_changed=0,source_GIS_overlays_repeated=0,coverage_diagnostic_threshold_not_admission_rule=True))
    log('80 ACS fixed-model predictions and20 declared coverage fits completed; no further fits.')

if __name__=='__main__':
    f,data,models=summarize();uncertainty_and_coverage(f,data,models)
