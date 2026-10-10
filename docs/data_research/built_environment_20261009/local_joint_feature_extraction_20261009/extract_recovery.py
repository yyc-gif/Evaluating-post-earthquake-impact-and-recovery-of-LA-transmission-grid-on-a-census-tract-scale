"""Extract and verify saved recovery metrics; no scientific stages are called."""
from pathlib import Path
import json,hashlib,sys,subprocess,itertools
import numpy as np,pandas as pd
from scipy import sparse,stats
from source_audit import ROOT,OUT,sha,dump
FORMAL=ROOT/'Formal_Experiment_20260923';INPUTS={}
def record(p):
 p=Path(p);INPUTS[str(p.relative_to(ROOT)) if ROOT in p.parents else str(p)]={'sha256':sha(p),'bytes':p.stat().st_size};return p
def read(p):
 p=record(p);d=pd.read_csv(p,dtype={'tract_id':str,'GEOID':str});d['tract_id']=d.tract_id.str.zfill(11);assert d.tract_id.str.fullmatch(r'06037\d{6}').all() and d.tract_id.is_unique;return d.set_index('tract_id')
def csv(n,d):d.to_csv(OUT/n,index=True if d.index.name=='tract_id' else False,na_rep='',float_format='%.15g',encoding='utf-8')
def summarize(name,x):
 x=pd.to_numeric(x,errors='coerce');v=x.dropna();qs=v.quantile([0,.01,.05,.25,.5,.75,.95,.99,1]).to_dict()
 return {'feature':name,'n':len(x),'nonmissing':len(v),'missing':int(x.isna().sum()),'zero_count':int(v.eq(0).sum()),'zero_fraction_observed':float(v.eq(0).mean()) if len(v) else None,'mean':float(v.mean()) if len(v) else None,'sd':float(v.std()) if len(v)>1 else None,'skewness':float(stats.skew(v,bias=False)) if len(v)>2 and v.std()>0 else None,**{f'q{int(q*100):02d}':float(y) for q,y in qs.items()}}
def recovery():
 full=read(FORMAL/'Stage 7 Output_SOVI_Harmonized/stage7_full_domain_tract_status.csv');res=read(FORMAL/'Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv'); assert len(full)==2315 and len(res)==2291
 m=pd.read_csv(record(ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv'),dtype={'tract_id':str,'substation_id':str});m.tract_id=m.tract_id.str.zfill(11);saved_order=pd.read_csv(record(ROOT/'Data/Tracts_Within_Expanded_Area.csv'),dtype={'GEOID':str});tracts=saved_order.GEOID.str.zfill(11).tolist();assert len(tracts)==len(set(tracts))==2315 and set(tracts)==set(full.index)
 with np.load(record(FORMAL/'Stage 1 Output_expanded/physical_inputs_2pc50.npz')) as z:stations=z['station_ids'].astype(str)
 wi={t:i for i,t in enumerate(tracts)};si={s:i for i,s in enumerate(stations)}
 W=sparse.csr_matrix((m.weight.to_numpy(float),([wi[t] for t in m.tract_id],[si[s] for s in m.substation_id])),shape=(2315,92));mass=np.asarray(W.sum(axis=1)).ravel();assert np.allclose(mass,1)
 src=FORMAL/'Formal_Offline_Evaluation/2pc50__C57_D1__direct-community__INTEGRALS.npz';manifest=json.loads(record(src.with_name('2pc50__C57_D1__direct-community__EVALUATION.json')).read_text(encoding='utf-8'));assert sha(src)==manifest['integral_sha256'];ident=manifest['identity'];assert ident['hazard']=='2pc50' and ident['resource_case']=='C57_D1' and ident['strategy']=='direct-community' and ident['H_eval_hr']==480
 with np.load(record(src)) as z:
  assert np.array_equal(z['station_ids'].astype(str),stations);B=z['M1_UTILITY_003__normalized_burden_hr']; L=z['G1_BASELINE_050__L_total'];physical_hashes=z['physical_hashes'].astype(str)
 assert B.shape==(1000,2315) and np.isfinite(B).all() and B.min()>=0 and B.max()<=480
 assert np.allclose(B,(W@L.T).T/mass,rtol=0,atol=1e-10)
 initial=np.zeros(92); times=[];changes=[];chain=hashlib.sha256();trajectory_audit=[];max_integral_error=0.;terminal_deficits=[]
 folder=FORMAL/'Formal_Trajectories/2pc50/C57_D1/direct-community'
 for i in range(1000):
  stem=f'2pc50__evaluation_{i:04d}';jp=record(folder/(stem+'.json'));raw=jp.read_bytes();q=json.loads(raw);chain.update(hashlib.sha256(raw).digest());idn=q['identity'];p=record(folder/(stem+'.npz'));assert sha(p)==q['npz_sha256']
  assert idn['hazard']=='2pc50' and idn['realization_id']==stem and idn['strategy']=='direct-community' and idn['resource_scenario']=='C57_D1' and idn['event_horizon_hr']==480 and idn['mapping_method_id']=='M1_UTILITY_003'
  assert idn['physical_sample_hash']==physical_hashes[i]
  with np.load(p) as z:
   assert np.array_equal(z['station_ids'].astype(str),stations);t=z['event_time_hr'];e=z['e'];total=z['L_total']
   assert t[0]==0 and t[-1]==480 and np.all(np.diff(t)>0) and np.isfinite(e).all()
   d=np.diff(e,axis=0);assert d.min()>=-1e-12;initial+=e[0];changed=(d!=0).any(axis=1);times.append(t[1:][changed]);changes.append(d[changed]);terminal_deficits.append(1-e[-1])
   direct=np.sum((1-e[:-1])*np.diff(t)[:,None],axis=0);error=float(np.max(np.abs(direct-L[i])));max_integral_error=max(max_integral_error,error);assert error<1e-10
  trajectory_audit.append({'realization_id':stem,'npz_sha256':sha(p),'physical_sample_hash':physical_hashes[i],'events':len(t),'integration_error_hr':error})
  if i%200==0:print('RECOVERY_ARCHIVES',i,flush=True)
 identity=json.loads(record(FORMAL/'FORMAL_STAGE7_INPUT_IDENTITY.json').read_text(encoding='utf-8'));assert chain.hexdigest()==identity['source_manifest_chain_sha256']
 init=W@(initial/1000);mean=np.array(init);t=np.concatenate(times);d=np.concatenate(changes,axis=0);sort=np.argsort(t,kind='stable');t=t[sort];d=d[sort];col=W.tocsc();cross=np.where(mean>=.8,0.,np.nan);start=0
 while start<len(t):
  end=int(np.searchsorted(t,t[start],side='right'));dv=d[start:end].sum(axis=0)/1000
  for station in np.flatnonzero(dv):
   lo,hi=col.indptr[station:station+2];mean[col.indices[lo:hi]]+=col.data[lo:hi]*dv[station]
  select=np.isnan(cross)&(mean>=.8);cross[select]=t[start];start=end
 expected=full.reindex(tracts);t_error=float(np.max(np.abs(cross-expected.T80.to_numpy())));init_error=float(np.max(np.abs(init-expected.Init_Supply.to_numpy())));assert t_error<1e-8 and init_error<1e-12
 frame=pd.DataFrame({'tract_id':tracts,'B_480_hr':B.mean(axis=0),'B_realization_sd_hr':B.std(axis=0,ddof=1),'B_p05_hr':np.quantile(B,.05,axis=0),'B_p95_hr':np.quantile(B,.95,axis=0),'B_unreached_horizon_fraction':np.mean((W@np.array(terminal_deficits).T).T/mass>.2,axis=0),'T80':cross,'Init_Supply':init,'AUC_480':1-B.mean(axis=0)/480,'residential_member':[x in res.index for x in tracts]}).set_index('tract_id')
 csv('RECOVERY_B_T80_INIT_COMPARISON.csv',frame);csv('RECOVERY_TRAJECTORY_IDENTITY_AUDIT.csv',pd.DataFrame(trajectory_audit))
 sub=frame.loc[res.index];summary=[summarize(k,sub[k]) for k in ['B_480_hr','T80','Init_Supply']];summary.append(summarize('log1p_B_480_hr',np.log1p(sub.B_480_hr)));csv('RECOVERY_DISTRIBUTION_QA.csv',pd.DataFrame(summary))
 pairs=[]
 for a,b in itertools.combinations(['B_480_hr','T80','Init_Supply'],2):
  v=sub[[a,b]].dropna();pairs.append({'a':a,'b':b,'n':len(v),'pearson_r':stats.pearsonr(v[a],v[b]).statistic,'spearman_rho':stats.spearmanr(v[a],v[b]).statistic})
 csv('RECOVERY_CORRELATIONS.csv',pd.DataFrame(pairs));csv('RECOVERY_EXTREMES.csv',sub.nlargest(20,'B_480_hr'))
 qa={'tract_count':2315,'residential_count':2291,'n_realizations':1000,'tract_order':'original row order of Data/Tracts_Within_Expanded_Area.csv, used by formal PreparedMapping; independently verified by W @ G1 integrals and saved Stage7 T80/initial values','B_missing_count':int(np.isnan(B).sum()),'T80_unreached_count':int(np.isnan(cross).sum()),'T80_source_definition':'first completion event at which mean of 1000 service trajectories reaches 0.8; NOT mean realization-specific T80','max_T80_reconstruction_error_hr':t_error,'max_initial_reconstruction_error':init_error,'max_station_integral_error_hr':max_integral_error,'max_terminal_station_deficit':float(np.max(terminal_deficits)),'source_manifest_chain_sha256':chain.hexdigest(),'scenario':'2pc50','resources':'C57_D1','strategy':'direct-community','mapping':'M1_UTILITY_003','gate':'G1_BASELINE_050','horizon_hr':480,'unmatched':[],'correlations':pairs,'distribution_summary':summary,'log_transform_adopted':False}
 dump('RECOVERY_EXTRACTION_QA.json',qa);dump('INPUT_SOURCE_HASHES.json',INPUTS)
 lines=['# Recovery metric extraction and validation','', 'B is the mean normalized cumulative modeled service deficit, integrated as previous-state steps over 0–480 h in each of the same 1,000 saved evaluation realizations. Mapping mass is unchanged. AUC_480 is exactly 1 - B_480_hr / 480 and is not an additional independent outcome.', '', 'T80 is the first exact completion-event time at which the **mean tract service trajectory** reaches 0.8. It is not the mean of individual-realization threshold crossings. The source implementation is src/la_grid/revision/formal/stage7.py; the legacy core KPI function also takes the first crossing of its supplied series. No Stage 3 Unconstrained result is used.', '', f'All 2,315 tracts match; the residential subset has exactly 2,291 original members. Recovery values are complete. Maximum saved-vs-reconstructed T80 error: {t_error:.3g} h; initial-service error {init_error:.3g}; station-integral error {max_integral_error:.3g} h. All 1,000 NPZ hashes and physical identities pass. All mean trajectories reach T80 before 480 h.', '', '| comparison | N | Pearson | Spearman |','|---|---:|---:|---:|']
 lines += [f"| {x['a']} vs {x['b']} | {x['n']} | {x['pearson_r']:.6f} | {x['spearman_rho']:.6f} |" for x in pairs]
 lines += ['',f"Raw B skewness = {summary[0]['skewness']:.6f}; log1p(B) skewness = {summary[-1]['skewness']:.6f}. Quantiles and extreme tracts are exported. This diagnoses long-tail compression without selecting a transform or a clustering feature. These correlations are descriptive tract associations, not independent causal evidence or a variable-selection rule."]
 (OUT/'RECOVERY_METRIC_QA.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print('RECOVERY_QA',json.dumps({k:v for k,v in qa.items() if k not in ['distribution_summary']}),flush=True)
if __name__=='__main__':recovery()
