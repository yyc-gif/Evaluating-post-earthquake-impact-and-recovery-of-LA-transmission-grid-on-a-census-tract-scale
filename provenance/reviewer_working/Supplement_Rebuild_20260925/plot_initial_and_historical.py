"""Plot-only projection of frozen unconstrained event states onto frozen M1 tracts."""
import csv
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Supplement_Rebuild_20260925'
FIG=OUT/'Figures'; TAB=OUT/'Tables'
FORMAL=ROOT/'Formal_Experiment_20260923'/'Formal_Trajectories'
HAZARDS=['Northridge','SanFernando','LongBeach','2pc50']
mapping=pd.read_csv(ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str,'substation_id':str})
mapping['tract_id']=mapping.tract_id.str.zfill(11)
tract_ids=sorted(mapping.tract_id.unique())
assert len(tract_ids)==2315
first=next((FORMAL/'Northridge'/'C57_D1'/'unconstrained').glob('*.npz'))
with np.load(first) as z: station_ids=list(z['station_ids'].astype(str))
assert len(station_ids)==92 and set(mapping.substation_id).issubset(station_ids)
ti={x:i for i,x in enumerate(tract_ids)};si={x:i for i,x in enumerate(station_ids)}
W=csr_matrix((mapping.weight.to_numpy(float),
    (mapping.tract_id.map(ti).to_numpy(),mapping.substation_id.map(si).to_numpy())),shape=(2315,92))
rowsums=np.asarray(W.sum(axis=1)).ravel()
assert np.allclose(rowsums,1,atol=1e-9)
rows=[]
for hazard in HAZARDS:
    folder=FORMAL/hazard/'C57_D1'/'unconstrained'
    paths=sorted(folder.glob('*.npz'))
    assert len(paths)==1000,(hazard,len(paths))
    initial_sum=np.zeros(2315); t80_sum=np.zeros(2315); reached=np.zeros(2315,dtype=int)
    for path in paths:
        with np.load(path) as z:
            assert list(z['station_ids'].astype(str))==station_ids
            times=z['event_time_hr']; assert len(times) and times[0]==0
            supply=W@z['e'].T
            initial_sum+=supply[:,0]
            above=supply>=0.8-1e-12
            reached_here=above.any(axis=1)
            idx=above.argmax(axis=1)
            t80_sum[reached_here]+=times[idx[reached_here]]
            reached+=reached_here
    for i,tract in enumerate(tract_ids):
        rows.append({'hazard':hazard,'tract_id':tract,'n_frozen_realizations':1000,
            'mean_initial_service_proxy':initial_sum[i]/1000,
            'mean_T80_hr_when_reached':t80_sum[i]/reached[i] if reached[i] else np.nan,
            'fraction_T80_reached':reached[i]/1000})
    print(hazard,'1000 frozen unconstrained archives projected',flush=True)
table=pd.DataFrame(rows)
table.to_csv(TAB/'S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv',index=False)

fig,ax=plt.subplots(figsize=(6.7,4))
for hazard in HAZARDS:
    vals=np.sort(table.loc[table.hazard==hazard,'mean_initial_service_proxy'].to_numpy())
    ax.plot(vals,np.arange(1,len(vals)+1)/len(vals),label=hazard)
ax.set(xlabel='Mean initial tract service-availability proxy',ylabel='Fraction of tracts',xlim=(0,1),ylim=(0,1))
ax.legend();fig.tight_layout()
fig.savefig(FIG/'S1_initial_service_CDF.png',dpi=300,bbox_inches='tight')
fig.savefig(FIG/'S1_initial_service_CDF.pdf',bbox_inches='tight');plt.close(fig)

tracts=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp')[['GEOID','geometry']]
tracts['tract_id']=tracts.GEOID.astype(str).str.zfill(11)
fig,axes=plt.subplots(2,2,figsize=(10,8))
for ax,hazard in zip(axes.flat,HAZARDS):
    frame=tracts.merge(table.loc[table.hazard==hazard,['tract_id','mean_initial_service_proxy']],on='tract_id',how='inner',validate='one_to_one')
    assert len(frame)==2315
    frame.plot(column='mean_initial_service_proxy',ax=ax,cmap='viridis',vmin=0,vmax=1,linewidth=0)
    ax.set_title(hazard);ax.axis('off')
fig.suptitle('Initial modeled service availability, 1,000-realization tract mean')
fig.subplots_adjust(right=.84,wspace=.12)
cax=fig.add_axes([.87,.22,.025,.55])
fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0,1),cmap='viridis'),cax=cax,label='Modeled service-availability proxy')
fig.savefig(FIG/'S1_initial_service_maps.png',dpi=300,bbox_inches='tight')
fig.savefig(FIG/'S1_initial_service_maps.pdf',bbox_inches='tight');plt.close(fig)

fig,axes=plt.subplots(2,2,figsize=(10,8))
for ax,hazard in zip(axes.flat,HAZARDS):
    frame=tracts.merge(table.loc[table.hazard==hazard,['tract_id','mean_T80_hr_when_reached']],on='tract_id',how='inner',validate='one_to_one')
    assert len(frame)==2315
    frame.plot(column='mean_T80_hr_when_reached',ax=ax,cmap='magma',vmin=0,vmax=80,linewidth=0,missing_kwds={'color':'#dddddd'})
    ax.set_title(hazard);ax.axis('off')
fig.suptitle('Unconstrained modeled tract T80, conditional mean when reached (h)')
fig.subplots_adjust(right=.84,wspace=.12)
cax=fig.add_axes([.87,.22,.025,.55])
fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0,80),cmap='magma'),cax=cax,label='Mean tract T80 when reached (h)')
fig.savefig(FIG/'S2_historical_unconstrained_T80_maps.png',dpi=300,bbox_inches='tight')
fig.savefig(FIG/'S2_historical_unconstrained_T80_maps.pdf',bbox_inches='tight');plt.close(fig)
print('PLOT_ONLY_COMPLETE',len(table))
