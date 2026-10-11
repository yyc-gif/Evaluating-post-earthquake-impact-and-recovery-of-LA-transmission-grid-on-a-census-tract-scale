from common import *
from measurement_resolution import PHYSICAL,PAIRS,partial
import numpy as np,pandas as pd,itertools
from scipy import stats

def main():
    d=pd.read_csv(lp(OUT/'SHORTLIST_FEATURE_MATRIX.csv'),dtype={'tract_id':str}).set_index('tract_id');cc=d.loc[d.common2286]
    core=['emc2022_total_built_land_fraction','housing_5plus_share','scag2020_classified_land_entropy'];rows=[]
    alternatives={'building_footprint_coverage':'emc2022_total_built_land_fraction','land_use_entropy':'scag2020_classified_land_entropy','housing_detached_share':'housing_5plus_share'}
    for c in PHYSICAL:
        controls=[x for x in core if x!=c and x!=alternatives.get(c)]+['SOVI_SCORE','log1p_BUILDVALUE'];z=cc[controls].to_numpy();z=np.column_stack([np.ones(len(z)),z]);y=cc[c].to_numpy();prediction=z@np.linalg.lstsq(z,y,rcond=None)[0];r2=1-np.square(y-prediction).sum()/np.square(y-y.mean()).sum()
        rows.append(dict(feature=c,n=len(cc),controls=';'.join(controls),linear_R2=r2,residual_variance_fraction=1-r2,conditional_VIF=1/(1-r2),residual_sd_raw_units=np.std(y-prediction,ddof=1),interpretation='conditional statistical redundancy; cannot establish or reject an independent construct'))
    save('INCREMENTAL_CONSTRUCT_INFORMATION.csv',rows)
    rows=[]
    for a,b,fam in PAIRS:
        controls=[c for c in core if c not in [a,b] and alternatives.get(a)!=c and alternatives.get(b)!=c]+['SOVI_SCORE','log1p_BUILDVALUE']
        rows.append(dict(family=fam,source_a=a,source_b=b,n=len(cc),controls=';'.join(controls),partial_pearson=partial(cc[a].to_numpy(),cc[b].to_numpy(),cc[controls].to_numpy())))
    save('SOURCE_SUBSTITUTION_PARTIAL_CORRELATIONS.csv',rows)
    # Missing-classified-land allocation bounds, not newly observed land uses.
    master=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_RESIDENTIAL_2291.csv').reindex(d.index)
    classes=['residential','commercial_office','industrial','institutional_public','transportation_utility','open_space_recreation','vacant_undeveloped','agriculture','mixed_use','under_construction','protected_undevelopable'];results=[]
    for year,prefix,area,land in [('2019','',master.land_use_classified_area_m2,master.land_geometry_area_m2),('2020','scag2020_',master.scag2020_classified_area_m2,master.scag2020_land_geometry_area_m2)]:
        a=master[[prefix+c+'_area_m2' for c in classes]].to_numpy();l=land.to_numpy();p=np.divide(a,l[:,None],out=np.full_like(a,np.nan),where=l[:,None]>0);missing=1-np.nansum(p,axis=1)
        low=p.copy();high=p.copy()
        for i in range(len(p)):
            if not np.isfinite(p[i]).all():continue
            low[i,np.argmax(p[i])]+=missing[i]
            # Max-entropy water filling; retain each observed category as a lower bound.
            left,right=0.,1.
            for _ in range(60):
                mid=(left+right)/2
                if np.maximum(p[i],mid).sum()>1:right=mid
                else:left=mid
            high[i]=np.maximum(p[i],(left+right)/2)
        def H(v):return -np.where(v>0,v*np.log(np.maximum(v,1e-300)),0).sum(axis=1)/np.log(11)
        lo,hi=H(low),H(high);lo[~np.isfinite(p).all(axis=1)]=np.nan;hi[~np.isfinite(p).all(axis=1)]=np.nan
        results.append(pd.DataFrame({'tract_id':master.index,'vintage':year,'classified_land_fraction':area/land,'observed_classified_entropy':master.land_use_entropy if year=='2019' else master.scag2020_classified_land_entropy,'possible_whole_land_entropy_lower':lo,'possible_whole_land_entropy_upper':hi,'bound_width':hi-lo}))
    save('SCAG_CLASSIFIED_LAND_SUPPORT_BOUNDS.csv',pd.concat(results,ignore_index=True))
    log('Conditional overlap and missing-land entropy bounds calculated without GIS or clustering reruns.')

if __name__=='__main__':main()
