"""Supplement aggregate ARI with raw class meaning and explicit split destinations."""
from common import *
from fit_weights import align
import numpy as np,pandas as pd,itertools
from sklearn.preprocessing import StandardScaler

def main():
    _,f,blocks,cases,_=inputs();sc=StandardScaler().fit(f[COLS]);zs=sc.transform(f[COLS]);archives={w:np.load(lp(OUT/'run_records'/(w+'.npz'))) for w in WEIGHTS};reference=archives['W1']['s42_labels'];allmask=np.ones(len(f),bool);targetids=json.loads(source(REVIEW+'D34_REFERENCE_IDENTITY.json').read_text())['tract_ids'];target=f.index.isin(targetids)
    contrasts=[];centers=[];minor_extra=[]
    for w,z in archives.items():
        for seed in SEEDS:
            y=z[f's{seed}_labels'];base=archives['W1'][f's{seed}_labels'];train=z[f's{seed}_train_mask'];pred=z[f's{seed}_spatial_prediction'];mapped,mp,_=align(y,pred,train);display,dm,_=align(reference,y,allmask);_,wbm,_=align(base,y,allmask)
            for k in range(4):
                m=y==k;new=mapped==k;retained=m&train;bb=base==wbm[k];mean=zs[m].mean(axis=0);newmean=zs[new].mean(axis=0);kept=zs[retained].mean(axis=0) if retained.any() else np.full(len(COLS),np.nan);oldmean=zs[bb].mean(axis=0)
                centers.append(dict(scheme=w,seed=seed,raw_class=k,W1_seed42_display_class=dm[k],vs_W1_z_center_distance=float(np.linalg.norm(mean-oldmean)),spatial_z_center_distance=float(np.linalg.norm(newmean-mean)),fixed_member_deletion_z_distance=float(np.linalg.norm(kept-mean)),replacement_vs_retained_z_distance=float(np.linalg.norm(newmean-kept)),common_W1_metric_spatial_center_distance=float(np.linalg.norm((newmean-mean)*factors('W1'))),reference_population=f.loc[m,'formal_population'].sum(),new_population=f.loc[new,'formal_population'].sum(),training_supported=bool(retained.any()),normalization='All centers are partition means in the common full-cohort StandardScaler coordinates; no cross-scheme weighted-center subtraction.'))
            for da,db in itertools.combinations(range(4),2):
                a=next(k for k,v in dm.items() if v==da);b=next(k for k,v in dm.items() if v==db)
                for c in COLS+['NRI_BUILDVALUE']:
                    olddiff=f.loc[y==a,c].mean()-f.loc[y==b,c].mean();newdiff=f.loc[mapped==a,c].mean()-f.loc[mapped==b,c].mean();contrasts.append(dict(scheme=w,seed=seed,W1_display_a=da,W1_display_b=db,feature=c,full_mean_difference=olddiff,spatial_mean_difference=newdiff,reversed=bool(olddiff*newdiff<0),display_rule='W1 seed42 overlap IDs for display; spatial mapping from own-full training overlap.'))
            for scope,labels,mask in [('full_fit',y,allmask),('spatial_all',mapped,allmask),('spatial_training',mapped,train),('spatial_heldout',mapped,~train)]:
                counts=np.bincount(labels[target&mask],minlength=4);largest=int(counts.argmax());classn=int(((labels==largest)&mask).sum())
                minor_extra.append(dict(scheme=w,seed=seed,scope=scope,number_of_destination_classes=int((counts>0).sum()),largest_destination_own_full_id=largest,largest_destination_original_members=int(counts[largest]),largest_destination_total_n=classn,largest_destination_purity=counts[largest]/classn if classn else np.nan,note='Largest destination is a descriptive destination count, not a new held-out matching rule.'))
    old=pd.read_csv(lp(OUT/'CORE3_34TRACT_AUDIT.csv'));enriched=old.merge(pd.DataFrame(minor_extra),on=['scheme','seed','scope'],validate='one_to_one');save('CORE3_34TRACT_AUDIT.csv',enriched)
    save('CORE3_CENTER_MEANING_SHIFTS.csv',centers);save('CORE3_ORIGINAL_UNIT_CLASS_CONTRASTS.csv',contrasts)
    q=pd.DataFrame(contrasts).groupby(['scheme','W1_display_a','W1_display_b','feature']).agg(cases=('reversed','size'),reversed_cases=('reversed','sum'),full_difference_median=('full_mean_difference','median'),full_difference_min=('full_mean_difference','min'),full_difference_max=('full_mean_difference','max'),spatial_difference_median=('spatial_mean_difference','median'),spatial_difference_min=('spatial_mean_difference','min'),spatial_difference_max=('spatial_mean_difference','max')).reset_index();assert q.cases.eq(20).all();save('CORE3_PROFILE_REVERSAL_SUMMARY.csv',q)
    log('Class-meaning shifts and minority destination splits audited; no held-out rematching and no new fit.')
if __name__=='__main__':main()
