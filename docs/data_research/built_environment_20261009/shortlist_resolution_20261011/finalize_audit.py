from common import *
import numpy as np,pandas as pd
from scipy import stats

def main():
    mat=pd.read_csv(lp(OUT/'SHORTLIST_FEATURE_MATRIX.csv'),dtype={'tract_id':str}).set_index('tract_id');d=mat.loc[mat.common2286];cols=['SOVI_SCORE','emc2022_total_built_land_fraction','housing_5plus_share','scag2020_classified_land_entropy','log1p_BUILDVALUE','ALR_NPCTL'];z=(d[cols]-d[cols].mean())/d[cols].std(ddof=0);rows=[]
    for c in cols:
        x=np.column_stack([np.ones(len(d)),z.drop(columns=c)]);y=z[c].to_numpy();p=x@np.linalg.lstsq(x,y,rcond=None)[0];r2=1-np.square(y-p).sum()/np.square(y).sum();rows.append(dict(feature=c,n=len(d),controls=';'.join([x for x in cols if x!=c]),conditional_R2=r2,residual_variance_fraction=1-r2,VIF=1/(1-r2),condition_number_standardized=np.linalg.cond(z.to_numpy()),interpretation='collinearity among simultaneous retained physical/social/economic coordinates; not causal attribution'))
    save('RISK_EXPOSURE_WITH_FIXED_PHYSICAL.csv',rows)
    f=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv');assert len(f)==2315 and f.residential_member.sum()==2291
    full=pd.DataFrame({'tract_id':f.index,'residential_member':f.residential_member.to_numpy(),'geometry_status':f.geometry_status.to_numpy(),'primary2287':f.index.isin(mat.index[mat.primary2287]),'common2286':f.index.isin(mat.index[mat.common2286]),'population':f.formal_population.to_numpy()});save('FULL_DOMAIN_ACCOUNTING.csv',full)
    q=pd.read_csv(lp(OUT/'SHORTLIST_MEASUREMENT_QA.csv'));original=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_RESIDENTIAL_2291.csv')
    for i,row in q.iterrows():
        key=row['coverage_column']
        if isinstance(key,str) and key in original:
            v=original[key];q.loc[i,'support_observations']=v.notna().sum();q.loc[i,'support_min']=v.min();q.loc[i,'support_p10']=v.quantile(.1);q.loc[i,'support_median']=v.median();q.loc[i,'support_p90']=v.quantile(.9);q.loc[i,'support_max']=v.max();q.loc[i,'support_meaning']=key
    save('SHORTLIST_MEASUREMENT_QA.csv',q)
    # Meaningful economic definitions for pairs involving controls, not empty metadata.
    stat=pd.read_csv(lp(OUT/'CANDIDATE_SOURCE_COMPARISON.csv'));reg=frame('candidate_admission_rebuild_20261010/CANDIDATE_REGISTER.csv')
    for side in ['a','b']:
        for c in ['SOVI_SCORE','log1p_BUILDVALUE','ALR_NPCTL','Pop_Density_per_km2']:
            mask=stat['feature_'+side].eq(c)
            rr=reg.loc[reg.candidate_id.eq('BUILDVALUE' if c=='log1p_BUILDVALUE' else c)]
            if len(rr):
                row=rr.iloc[0]
                for field in ['construct','definition','unit','vintage','source_url','source_commit']:stat.loc[mask,'source_'+side+'_'+field]=row[field]
            if c=='SOVI_SCORE':
                stat.loc[mask,'source_'+side+'_definition']='FEMA archived v1.19 published social-vulnerability percentile; mandatory independent coordinate';stat.loc[mask,'source_'+side+'_vintage']='Mar-23 v1.19';stat.loc[mask,'source_'+side+'_unit']='national percentile0-100'
            if c=='log1p_BUILDVALUE':stat.loc[mask,'source_'+side+'_definition']='ln(1 + BUILDVALUE in source dollar units); monetary asset stock, one transformed representation'
    save('CANDIDATE_SOURCE_COMPARISON.csv',stat)
    dump('DATA_ADMISSION_AND_SOURCE_QA.json',dict(reference_commit=BASELINE,source_registry_n=64,full_domain_n=2315,residential_master_n=2291,primary_n=2287,conditional_age_pair_n=2286,unclassified_geometry=UNRESOLVED,conditional_age_missing=['06037115103'],final_cluster_labels_promoted=False,source_lineage_note='Official LARIAC enrichment schema includes parcel/assessment fields; exact historical join/cardinality remains unresolved, no independent age-source validation claimed.'))
    log('Completed whole-domain accounting, support summaries and stock/loss conditional diagnostics.')

if __name__=='__main__':main()
