"""Membership, original-unit meaning and variance decomposition; no model fitting."""
from common import *
from fit_weights import align
import numpy as np,pandas as pd,itertools
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler
from scipy import stats

PROFILE=COLS+['NRI_BUILDVALUE','T80','scag2020_classified_land_coverage']

def summary_values(v):
    v=pd.Series(v).dropna();return dict(mean=v.mean(),median=v.median(),p10=v.quantile(.1),p90=v.quantile(.9),valid_n=len(v),zero_fraction=v.eq(0).mean())
def class_metrics(base,pred,train,ctx):
    mapped,mp,tab=align(base,pred,train);rows=[];tables=[]
    for scope,mask in [('all',np.ones(len(base),bool)),('training',train),('heldout',~train)]:
        raw=np.zeros((4,4),int);np.add.at(raw,(base[mask],pred[mask]),1)
        for a,b in itertools.product(range(4),repeat=2):tables.append(dict(**ctx,scope=scope,baseline_raw_class=a,predicted_raw_class=b,n=raw[a,b],training_selected_map_to_baseline=mp[b]))
        for k in range(4):
            old=(base==k)&mask;new=(mapped==k)&mask;inter=int((old&new).sum());union=int((old|new).sum());bn=int(old.sum());pn=int(new.sum());supported=bool((base[train]==k).any())
            outgoing=np.bincount(mapped[old],minlength=4);incoming=np.bincount(base[new],minlength=4);offout=outgoing.copy();offout[k]=0;offin=incoming.copy();offin[k]=0
            rows.append(dict(**ctx,scope=scope,baseline_raw_class=k,baseline_n=bn,baseline_training_n=int((base[train]==k).sum()),predicted_n=pn,intersection=inter,union=union,retention=inter/bn if bn else np.nan,purity=inter/pn if pn else np.nan,Jaccard=inter/union if union else np.nan,training_supported=supported,matched_predicted_raw_class=next(a for a,b in mp.items() if b==k),outgoing_counts=json.dumps(outgoing.tolist()),incoming_counts=json.dumps(incoming.tolist()),largest_other_outflow_class=int(offout.argmax()) if offout.max() else None,largest_other_outflow_n=int(offout.max()),largest_other_inflow_class=int(offin.argmax()) if offin.max() else None,largest_other_inflow_n=int(offin.max()),interpretation='Matching chosen only from training overlap; unsupported matches have no learned class interpretation.'))
    return mapped,mp,rows,tables

def main():
    _,f,blocks,cases,_=inputs();archives={w:np.load(lp(OUT/'run_records'/(w+'.npz'))) for w in WEIGHTS};runs=pd.read_csv(lp(OUT/'CORE3_RUN_SUMMARY.csv'));sc=StandardScaler().fit(f[COLS]);zs=sc.transform(f[COLS]);rawstd=f[PROFILE].std(ddof=0);reference=archives['W1']['s42_labels'];allmask=np.ones(len(f),bool)
    pop=f.formal_population.to_numpy();targetids=json.loads(source(REVIEW+'D34_REFERENCE_IDENTITY.json').read_text())['tract_ids'];target=f.index.isin(targetids);assert target.sum()==34
    seedpairs=[];contrasts=[];transitions=[];sizes=[];profiles=[];domainrows=[];featurerows=[];spatialmetrics=[];spatialct=[];small=[];spatialprofiles=[];stockrows=[];geographic=[];predictions=[];boundary=[];pattern=[];direction=[]
    for w,z in archives.items():
        fac=factors(w);x=zs*fac
        for a,b in itertools.combinations(SEEDS,2):seedpairs.append(dict(scheme=w,seed_a=a,seed_b=b,ARI=adjusted_rand_score(z[f's{a}_labels'],z[f's{b}_labels'])))
        for seed in SEEDS:
            y=z[f's{seed}_labels'];base=archives['W1'][f's{seed}_labels'];display,displaymp,displaytab=align(reference,y,allmask);train=z[f's{seed}_train_mask'];pred=z[f's{seed}_spatial_prediction'];mapped,mp,metrics,tables=class_metrics(y,pred,train,dict(scheme=w,seed=seed));spatialmetrics+=metrics;spatialct+=tables
            aligned,wm,ct=align(base,y,allmask);basemap,_,_=align(reference,base,allmask)
            contrasts.append(dict(scheme=w,seed=seed,ARI_vs_W1=adjusted_rand_score(base,y),reassigned_n=int((aligned!=base).sum()),reassigned_fraction=float((aligned!=base).mean())))
            for i,j in itertools.product(range(4),repeat=2):transitions.append(dict(scheme=w,seed=seed,W1_same_seed_raw_class=i,W1_seed42_display_class=int(basemap[np.flatnonzero(base==i)[0]]),scheme_raw_class=j,scheme_W1_overlap_display_class=displaymp[j],n=ct[i,j],fraction_of_W1_class=ct[i,j]/(base==i).sum(),fraction_of_scheme_class=ct[i,j]/(y==j).sum()))
            for k in range(4):
                mask=y==k;d=f.loc[mask];sizes.append(dict(scheme=w,seed=seed,raw_class=k,W1_seed42_display_class=displaymp[k],n=int(mask.sum()),tract_share=mask.mean(),population=pop[mask].sum(),population_share=pop[mask].sum()/pop.sum()))
                for c in PROFILE:profiles.append(dict(scheme=w,seed=seed,raw_class=k,W1_seed42_display_class=displaymp[k],feature=c,statistic_weight='unweighted_tract',**summary_values(d[c])))
                basek=next(a for a,b in wm.items() if a==k);refclass=wm[k];bm=base==refclass
                for c in ['log1p_BUILDVALUE','NRI_BUILDVALUE','ALR_NPCTL']:
                    stockrows.append(dict(scheme=w,seed=seed,W1_same_seed_reference_class=refclass,scheme_raw_class=k,n=int(mask.sum()),reference_n=int(bm.sum()),population=pop[mask].sum(),feature=c,mean=d[c].mean(),median=d[c].median(),reference_mean=f.loc[bm,c].mean(),reference_median=f.loc[bm,c].median(),mean_change=d[c].mean()-f.loc[bm,c].mean(),median_change=d[c].median()-f.loc[bm,c].median(),economic_parent_combined_weight=WEIGHTS[w][-1]+WEIGHTS[w][-2],interpretation='Changing membership and weights; original-unit descriptions, not per-tract value changes.'))
            # Exact weighted-variance decomposition uses partition means, not fitted centers.
            centered=x-x.mean(axis=0);tss=np.square(centered).sum(axis=0);bss=sum((y==k).sum()*np.square(x[y==k].mean(axis=0)-x.mean(axis=0)) for k in range(4));wss=sum(np.square(x[y==k]-x[y==k].mean(axis=0)).sum(axis=0) for k in range(4));assert np.allclose(tss,bss+wss,rtol=1e-11,atol=1e-10)
            for i,c in enumerate(COLS):
                dom=next(d for d,v in DOMAIN_COLUMNS.items() if c in v);featurerows.append(dict(scheme=w,seed=seed,domain=dom,feature=c,nominal_squared_weight=fac[i]**2,standardized_multiplier=fac[i],TSS=tss[i],BSS=bss[i],WSS=wss[i],feature_between_fraction=bss[i]/bss.sum(),feature_explained_fraction=bss[i]/tss[i],weighted_total_fraction=tss[i]/tss.sum(),center_provenance='Partition means used for sums of squares; estimator centers separately preserved.'))
            for dom,coords in DOMAIN_COLUMNS.items():
                ii=[COLS.index(c) for c in coords];dt=tss[ii].sum();db=bss[ii].sum();dw=wss[ii].sum();domainrows.append(dict(scheme=w,seed=seed,domain=dom,nominal_squared_budget=sum(fac[ii]**2),TSS=dt,BSS=db,WSS=dw,domain_between_fraction=db/bss.sum(),domain_explained_fraction=db/dt,within_fraction=dw/dt,partition_total_BSS=bss.sum(),partition_total_TSS=tss.sum()))
            # The minority audit follows the own-full dominant destination through the training-only map.
            fullcounts=np.bincount(y[target],minlength=4);dominant=int(fullcounts.argmax())
            for scope,labels,mask in [('full_fit',y,allmask),('spatial_all',mapped,allmask),('spatial_training',mapped,train),('spatial_heldout',mapped,~train)]:
                group=(labels==dominant)&mask;members=target&mask;inter=int((group&members).sum());pn=int(group.sum());tn=int(members.sum());union=int((group|members).sum())
                small.append(dict(scheme=w,seed=seed,scope=scope,reference_group_n=34,reference_members_in_scope=tn,reference_group_training_n=int((target&train).sum()),full_dominant_raw_class=dominant,dominant_class_training_supported=bool((y[train]==dominant).any()),full_reference_destination_counts=json.dumps(fullcounts.tolist()),destination_counts_in_own_full_class_ids=json.dumps(np.bincount(labels[members],minlength=4).tolist()),dominant_intersection=inter,predicted_dominant_class_n=pn,original_members_outside_dominant=tn-inter,additional_tracts_absorbed=pn-inter,retention=inter/tn if tn else np.nan,purity=inter/pn if pn else np.nan,Jaccard=inter/union if union else np.nan,removed_blocks=';'.join(cases[seed]),comparison='Exact historical34 GEOIDs; follow own-full dominant class through training-overlap spatial mapping.'))
            # Fixed-reference membership deletion versus membership replacement.
            for k in range(4):
                original=y==k;retained=original&train;new=mapped==k;matched_training=new&train
                for c in PROFILE:
                    before=f.loc[original,c].mean();kept=f.loc[retained,c].mean();newmean=f.loc[new,c].mean()
                    for scope,selection in [('matched_all',new),('fixed_members_training',retained),('matched_training',matched_training)]:
                        v=f.loc[selection,c];mean=v.mean();spatialprofiles.append(dict(scheme=w,seed=seed,baseline_raw_class=k,W1_seed42_display_class=displaymp[k],profile_population=scope,feature=c,n=int(selection.sum()),baseline_mean=before,mean=mean,median=v.median(),p10=v.quantile(.1),p90=v.quantile(.9),mean_change_raw=mean-before,mean_change_standardized=(mean-before)/rawstd[c] if rawstd[c]>0 else np.nan,fixed_member_deletion_change=kept-before,replacement_vs_retained_change=newmean-kept,training_supported=bool(retained.any())))
            # Geography/margin diagnostics do not declare a data-driven boundary threshold.
            dd=np.sort(np.square(x[:,None,:]-z[f's{seed}_centers'][None,:,:]).sum(axis=2),axis=1);margin=dd[:,1]-dd[:,0];changed=mapped!=y
            for state in [False,True]:
                v=margin[changed==state];boundary.append(dict(scheme=w,seed=seed,comparison='own-full versus spatial',changed=state,n=len(v),full_squared_distance_margin_mean=v.mean() if len(v) else None,full_squared_distance_margin_median=np.median(v) if len(v) else None))
            for block,g in blocks.groupby('block_id'):
                ii=f.index.get_indexer(g.index);geographic.append(dict(scheme=w,seed=seed,block_id=block,removed_block=block in cases[seed],n=len(ii),spatial_changed_n=int(changed[ii].sum()),spatial_changed_fraction=changed[ii].mean(),vs_W1_changed_n=int((aligned[ii]!=base[ii]).sum()),reference34_n=int(target[ii].sum())))
            for i,t in enumerate(f.index):predictions.append(dict(scheme=w,seed=seed,tract_id=t,block_id=blocks.block_id.iloc[i],full_raw_class=int(y[i]),W1_seed42_display_class=int(display[i]),spatial_raw_class=int(pred[i]),spatial_own_full_aligned_class=int(mapped[i]),training=bool(train[i]),reference34=bool(target[i])))
            # Class meaning is compared in raw units; no causality or accuracy claim.
            means=np.array([f.loc[y==k,COLS].mean().to_numpy() for k in range(4)]);spmeans=np.array([f.loc[mapped==k,COLS].mean().to_numpy() for k in range(4)])
            highestB=int(means[:,COLS.index('B_480_hr')].argmax());highestS=int(means[:,COLS.index('SOVI_SCORE')].argmax());pattern.append(dict(scheme=w,seed=seed,max_B_raw_class=highestB,max_SOVI_raw_class=highestS,max_B_is_max_SOVI=highestB==highestS,max_B_class_n=int((y==highestB).sum()),max_B_class_B=means[highestB,0],max_B_class_SOVI=means[highestB,COLS.index('SOVI_SCORE')],max_SOVI_class_B=means[highestS,0]))
            for a,b in itertools.combinations(range(4),2):
                for j,c in enumerate(COLS):
                    olddiff=means[a,j]-means[b,j];newdiff=spmeans[a,j]-spmeans[b,j];direction.append(dict(scheme=w,seed=seed,class_a=a,class_b=b,W1_display_a=displaymp[a],W1_display_b=displaymp[b],feature=c,full_difference=olddiff,spatial_difference=newdiff,reversed=bool(olddiff*newdiff<0)))
        log(f'{w}: membership/profile/domain/minority diagnostics summarized without fitting.')
    save('CORE3_SEED_PAIR_ARI.csv',seedpairs);save('CORE3_SAME_SEED_W1_COMPARISONS.csv',contrasts);save('CORE3_WEIGHT_CLASS_TRANSITIONS.csv',transitions);save('CORE3_CLASS_SIZES_AND_POPULATION.csv',sizes);save('CORE3_CLASS_PROFILES.csv',profiles);save('CORE3_DOMAIN_SEPARATION.csv',domainrows);save('CORE3_FEATURE_DISTANCE_CONTRIBUTIONS.csv',featurerows);save('CORE3_SPATIAL_CLASS_METRICS.csv',spatialmetrics);save('CORE3_SPATIAL_RAW_CONTINGENCIES.csv',spatialct);save('CORE3_34TRACT_AUDIT.csv',small);save('CORE3_SPATIAL_PROFILE_STABILITY.csv',spatialprofiles);save('CORE3_STOCK_ALR_WEIGHT_EFFECTS.csv',stockrows);save('CORE3_GEOGRAPHIC_REASSIGNMENT.csv',geographic);save('CORE3_BOUNDARY_MARGIN_DIAGNOSTICS.csv',boundary);save('CORE3_TRACT_PREDICTIONS.csv',predictions);save('CORE3_CLASS_MEANING_PATTERNS.csv',pattern);save('CORE3_PROFILE_DIRECTION_STABILITY.csv',direction)
    pdomain=pd.DataFrame(domainrows);pf=pd.DataFrame(featurerows);minor=pd.DataFrame(small);pair=pd.DataFrame(seedpairs);contrast=pd.DataFrame(contrasts);out=[]
    for w in WEIGHTS:
        r=runs.loc[runs.scheme.eq(w)];s=pair.loc[pair.scheme.eq(w),'ARI'];c=contrast.loc[contrast.scheme.eq(w)];m=minor.loc[minor.scheme.eq(w)&minor.scope.eq('spatial_all')]
        out.append(dict(scheme=w,seed_pair_ARI_median=s.median(),seed_pair_ARI_min=s.min(),seed_pair_ARI_p05=s.quantile(.05),W1_same_seed_ARI_median=c.ARI_vs_W1.median(),W1_same_seed_ARI_min=c.ARI_vs_W1.min(),reassigned_n_median=c.reassigned_n.median(),reassigned_n_max=c.reassigned_n.max(),reassigned_fraction_median=c.reassigned_fraction.median(),spatial_ARI_median=r.spatial_ARI_all.median(),spatial_ARI_p05=r.spatial_ARI_all.quantile(.05),spatial_ARI_min=r.spatial_ARI_all.min(),spatial_ARI_max=r.spatial_ARI_all.max(),spatial_changed_n_max=r.aligned_reassigned_n.max(),minority_retention_min=m.retention.min(),minority_purity_min=m.purity.min(),minority_predicted_n_max=m.predicted_dominant_class_n.max(),unsupported_minor_cases=int((~m.dominant_class_training_supported).sum())))
    save('CORE3_WEIGHT_COMPARISONS.csv',out)
    save('CORE3_WEIGHT_SPATIAL_STABILITY.csv',runs[['scheme','seed','training_n','heldout_n','removed_blocks','spatial_ARI_all','spatial_ARI_training','spatial_ARI_heldout','aligned_reassigned_n','unsupported_training_classes','spatial_inertia','spatial_iterations']])
    save('CORE3_DOMAIN_SEPARATION_SUMMARY.csv',pdomain.groupby(['scheme','domain']).agg(nominal_squared_budget=('nominal_squared_budget','first'),between_median=('domain_between_fraction','median'),between_min=('domain_between_fraction','min'),between_max=('domain_between_fraction','max'),explained_median=('domain_explained_fraction','median'),within_median=('within_fraction','median')).reset_index())
    # Shared linear information is a measurement diagnostic, not cause/importance.
    overlap=[]
    for targetcols,controls,title in [(DOMAIN_COLUMNS['Grid'],DOMAIN_COLUMNS['Recovery'],'grid_given_recovery'),(DOMAIN_COLUMNS['Recovery'],DOMAIN_COLUMNS['Grid'],'recovery_given_grid')]:
        xx=np.column_stack([np.ones(len(f)),zs[:,[COLS.index(c) for c in controls]]])
        for c in targetcols:
            yy=zs[:,COLS.index(c)];res=yy-xx@np.linalg.lstsq(xx,yy,rcond=None)[0];r2=1-np.square(res).sum()/np.square(yy-yy.mean()).sum();overlap.append(dict(analysis=title,feature=c,controls=';'.join(controls),n=len(f),linear_R2=r2,residual_variance_fraction=1-r2,interpretation='In-sample linear shared-information diagnostic; not causal or independent validation.'))
    save('CORE3_GRID_RECOVERY_INFORMATION_OVERLAP.csv',overlap)
    reversals=pd.DataFrame(direction).groupby(['scheme','W1_display_a','W1_display_b','feature']).agg(cases=('reversed','size'),reversed_cases=('reversed','sum'),baseline_diff_median=('full_difference','median'),spatial_diff_median=('spatial_difference','median')).reset_index();save('CORE3_PROFILE_REVERSAL_SUMMARY.csv',reversals)
    dump('SUMMARY_QA.json',dict(schemes=5,full_seed_records=100,spatial_records=100,pairwise_seed_ARIs=len(pair),all_class_transition_cells=len(transitions),spatial_raw_cells=len(spatialct),master_n=2291,primary_n=2287,reference34_GEOIDs=targetids,all_decompositions_verified=True,statistics='Empirical summaries, not confidence intervals; 20 deletion cases but 17 unique geographic sets.',new_fits_in_summarization=0))
    log('All controlled-weight summaries completed. No new fits.')
if __name__=='__main__':main()
