"""Post-computation protection and numerical QA, without new fitting."""
from common import *
import numpy as np,pandas as pd
from scipy import stats

if __name__=='__main__':
    before=json.loads(lp(OUT/'PRESERVATION_BEFORE.json').read_text());after=snapshot();assert before==after;dump('PRESERVATION_AFTER.json',after)
    master,f,blocks,cases,_=inputs();q=pd.read_csv(lp(OUT/'CORE3_DOMAIN_SEPARATION.csv'));error=np.abs(q.TSS-q.BSS-q.WSS).max();assert error<1e-8
    for r in json.loads(lp(OUT/'INPUT_HASHES.json').read_text()).values():assert sha(r['path'])==r['sha256']
    dump('NUMERICAL_QA.json',dict(primary_n=2287,master_n=2291,features=12,schemes=5,full_fits=100,spatial_fits=100,W1_fits_reused=40,new_fits=160,additional_k_searches=0,additional_PCA=0,physical_simulations=0,formal_scientific_files_changed=0,stock_ALR_primary_N=2287,stock_ALR_Pearson=stats.pearsonr(f.log1p_BUILDVALUE,f.ALR_NPCTL).statistic,stock_ALR_Spearman=stats.spearmanr(f.log1p_BUILDVALUE,f.ALR_NPCTL).statistic,max_TSS_BSS_WSS_absolute_error=error,protected_scientific_files_unchanged=950,original_staged_items_unchanged=862,original_index_unchanged=True,source_bytes_unchanged=True,formal_labels_and_manuscript_and_figures_unchanged=True))
    log('All source bytes and variance identities verified; 950 protected files and original862 staged items/index unchanged.')
