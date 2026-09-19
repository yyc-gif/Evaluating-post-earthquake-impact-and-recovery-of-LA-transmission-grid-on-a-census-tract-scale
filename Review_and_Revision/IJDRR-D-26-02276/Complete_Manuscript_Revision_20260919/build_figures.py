"""Manuscript figures from retained statistics only; no scientific execution."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT=Path(__file__).resolve().parent
SRC=OUT.parent/'Targeted_Methodological_Strengthening_20260919'
R26=OUT.parent/'26_GA_Reproducibility_and_Revised_Paired_Pilot_20260919'
F=OUT/'Figures';F.mkdir(exist_ok=True)
S=['Hospital-first','GA-Balanced','GA-HospFirst','GA-Efficiency']
LAB=['Hospital-first','Balanced','HospFirst','Efficiency']
COL=['#333333','#0072B2','#009E73','#D55E00']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,'axes.titlesize':11,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.facecolor':'white'})
d=pd.read_csv(SRC/'METRIC_DISTRIBUTIONS.csv')
e=pd.read_csv(SRC/'PAIRED_EFFECTS.csv')
w=pd.read_csv(SRC/'WINNER_LOSER_POPULATION.csv')
def mean(c,s,m):return float(d[(d.condition==c)&(d.strategy==s)&(d.metric==m)].iloc[0]['mean'])
def effect(c,s,m):return e[(e.contrast=='strategy_minus_HF')&(e.condition==c)&(e.strategy==s)&(e.metric==m)].iloc[0]
def save(fig,name):
 fig.savefig(F/(name+'.png'),dpi=220,bbox_inches='tight');fig.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close(fig)

fig,ax=plt.subplots(figsize=(9,4.8));ax.set(xlim=(0,10),ylim=(0,6));ax.axis('off')
boxes=[(.2,4.3,3,1.3,'Shared physical inputs','302 assets; 32 paired realizations\n57 crews; directed travel'),(3.8,4.3,2.5,1.3,'Four fixed sequences','Hospital-first; two initializers\nEfficiency search'),(7,4.3,2.8,1.3,'Event logistics','DS > 0 queue; earliest free crew\nCompletion releases crew'),(7,2.2,2.8,1.3,'Availability proxy','Completion-step raw state\nFixed source-component gate'),(3.8,2.2,2.5,1.3,'SCE candidates','113 identity; 71 proxy\n12 unresolved; weights fixed'),(.2,2.2,3,1.3,'Tract outcomes','817 tracts; resolved burden\nGroups, Gini, local effects')]
for x,y,b,h,title,body in boxes:
 ax.add_patch(FancyBboxPatch((x,y),b,h,boxstyle='round,pad=.05',linewidth=.8,edgecolor='#7b8790',facecolor='#f5f7f8'))
 ax.text(x+b/2,y+h-.27,title,ha='center',weight='bold',fontsize=10)
 ax.text(x+b/2,y+.47,body,ha='center',va='center',fontsize=8.8,linespacing=1.4)
for start,end in [((3.25,4.95),(3.73,4.95)),((6.35,4.95),(6.94,4.95)),((8.4,4.2),(8.4,3.58)),((6.94,2.85),(6.36,2.85)),((3.73,2.85),(3.26,2.85))]:
 ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',lw=1.3,color='#333333'))
ax.text(.25,1.32,'Two separate contrasts',weight='bold',fontsize=11)
ax.text(.25,.72,'A/B relative influence 0.5 or 2: offline burden evaluation only\nDS4 stored duration ×2: reexecute logistics and propagation; no new draws',fontsize=10,linespacing=1.5)
save(fig,'Figure_1_Study_design')

fig,axs=plt.subplots(2,2,figsize=(9,7),layout='constrained');x=np.arange(1,5)
for s,l,c in zip(S,LAB,COL):axs[0,0].plot(x,[mean('corrected_baseline',s,f'Q{k}_burden_hr') for k in x],'-o',label=l,color=c)
axs[0,0].set(title='A  Absolute group burden',xticks=x,xticklabels=['Q1','Q2','Q3','Q4'],ylabel='Population-weighted normalized burden (h)');axs[0,0].legend(fontsize=8,ncol=2)
for offset,s,c in [(-.08,S[1],COL[1]),(.08,S[2],COL[2])]:
 rows=[effect('corrected_baseline',s,f'Q{k}_burden_hr') for k in x]
 y=np.array([r.mean_paired_difference for r in rows]);lo=np.array([r.ci95_low for r in rows]);hi=np.array([r.ci95_high for r in rows])
 axs[0,1].errorbar(x+offset,y,yerr=[y-lo,hi-y],fmt='o',capsize=3,color=c,label=s[3:])
axs[0,1].axhline(0,color='#999999',lw=.8);axs[0,1].set(title='B  Small group shifts versus Hospital-first',xticks=x,xticklabels=['Q1','Q2','Q3','Q4'],ylabel='Paired difference (h)');axs[0,1].legend(fontsize=8)
rows=[effect('corrected_baseline',S[3],f'Q{k}_burden_hr') for k in x];y=np.array([r.mean_paired_difference for r in rows])
axs[1,0].bar(x,y,color=COL[3],width=.6);axs[1,0].errorbar(x,y,yerr=[y-np.array([r.ci95_low for r in rows]),np.array([r.ci95_high for r in rows])-y],fmt='none',ecolor='#333333',capsize=3)
axs[1,0].set(title='C  Efficiency excess burden in every group',xticks=x,xticklabels=['Q1','Q2','Q3','Q4'],ylabel='Paired difference from Hospital-first (h)',ylim=(0,25))
for s,l,c in zip(S,LAB,COL):
 xx=mean('corrected_baseline',s,'burden_gini');yy=mean('corrected_baseline',s,'population_normalized_burden_hr');axs[1,1].scatter(xx,yy,c=c,s=55)
 offsets={'Hospital-first':(-90,12),'Balanced':(-83,-18),'HospFirst':(8,-1),'Efficiency':(8,0)}
 axs[1,1].annotate(l,(xx,yy),xytext=offsets[l],textcoords='offset points',fontsize=8,color=c)
axs[1,1].set(title='D  Lower inequality need not mean less burden',xlabel='Mean population-weighted Gini',ylabel='Mean population-normalized burden (h)',xlim=(.17,.238),ylim=(41,62))
save(fig,'Figure_2_Group_burdens')

fig,axs=plt.subplots(2,1,figsize=(8.6,5.8),layout='constrained');classes=['improved','near_zero','worsened','unresolved'];cc=['#0072B2','#dddddd','#D55E00','#555555']
for a,stat,title in zip(axs,['classification_of_32_realization_mean','single_realization_classification'],['A  Classify each tract by its 32-realization mean effect','B  Classify within each realization then average population shares']):
 sub=w[(w.condition=='corrected_baseline')&(w.group=='ALL')&(w.statistic==stat)]
 left=np.zeros(3)
 for cat,color in zip(classes,cc):
  vals=np.array([sub[(sub.strategy==s)&(sub.classification==cat)].pct_all_group_population.mean() for s in S[1:]])
  a.barh(LAB[1:],vals,left=left,color=color,label=cat.replace('_','-'))
  for j,v in enumerate(vals):
   if v>5:a.text(left[j]+v/2,j,f'{v:.1f}%',ha='center',va='center',color='white' if color in [cc[0],cc[2],cc[3]] else 'black',fontsize=9)
  left+=vals
 a.set(title=title,xlim=(0,100),xlabel='Share of all 3,572,152 people (%)');a.invert_yaxis()
axs[0].legend(ncol=4,loc='lower center',bbox_to_anchor=(.5,1.05),frameon=False,fontsize=8)
save(fig,'Figure_3_Tract_classification')

fig,axs=plt.subplots(2,2,figsize=(9,7),layout='constrained');cs=['AB_lambda_0.5','corrected_baseline','AB_lambda_2'];ls=[.5,1,2]
axs[0,0].plot(ls,[effect(c,S[3],'Q4_burden_hr').mean_paired_difference for c in cs],'-o',color=COL[3]);axs[0,0].set(title='A  Candidate influence and Q4 excess burden',xlabel='Relative Class B influence λ',ylabel='Efficiency − Hospital-first (h)',xticks=ls)
for s,l,c in zip(S,LAB,COL):axs[0,1].plot(ls,[mean(cond,s,'Q4_minus_Q1_burden_gap_hr') for cond in cs],'-o',color=c,label=l)
axs[0,1].axhline(0,color='#999999',lw=.8);axs[0,1].set(title='B  Some group relationships depend on λ',xlabel='Relative Class B influence λ',ylabel='Mean signed Q4 − Q1 gap (h)',xticks=ls);axs[0,1].legend(fontsize=8,ncol=2)
for s,l,c in zip(S[1:],LAB[1:],COL[1:]):
 vals=[effect(cond,s,'population_normalized_burden_hr').mean_paired_difference for cond in ['corrected_baseline','DS4x2']]
 axs[1,0].plot([0,1],vals,'-o',label=l,color=c)
axs[1,0].axhline(0,color='#999999',lw=.8);axs[1,0].set(title='C  Relative severe-damage duration matters',xticks=[0,1],xticklabels=['Baseline','DS4 ×2'],ylabel='Population burden difference from HF (h)');axs[1,0].legend(fontsize=8)
for s,l,c in zip(S,LAB,COL):axs[1,1].plot(x,[mean('DS4x2',s,f'Q{k}_burden_hr') for k in x],'-o',color=c,label=l)
axs[1,1].set(title='D  Absolute group burdens under DS4 ×2',xticks=x,xticklabels=['Q1','Q2','Q3','Q4'],ylabel='Population-weighted normalized burden (h)');axs[1,1].legend(fontsize=8,ncol=2)
save(fig,'Figure_4_Targeted_contrasts')

g=pd.read_csv(R26/'GA_CONVERGENCE_BY_SEED.csv')
fig,axs=plt.subplots(3,1,figsize=(8.6,7),layout='constrained')
for ax,s in zip(axs,[S[1],S[2],S[3]]):
 sub=g[g.policy==s]
 for seed,gg in sub.groupby('seed'):ax.plot(gg.generation,gg.generation_best_fitness,lw=.75,alpha=.65,label=str(seed))
 selected={'GA-Balanced':.7936901220040734,'GA-HospFirst':.9164599461760283,'GA-Efficiency':.3682723546370179}[s]
 ax.axhline(selected,color='black',ls='--',lw=1,label='Adopted candidate score')
 ax.set(title=s.replace('GA-','')+' objective',xlabel='Generation',ylabel='Generation-best fitness')
axs[0].legend(ncol=6,fontsize=7,loc='lower center',bbox_to_anchor=(.5,1.13),frameon=False)
save(fig,'Figure_S1_Search_records')

gg=pd.read_csv(SRC/'GROUP_ABSOLUTE_BURDEN.csv');tiers=['S1_DIRECT_ONLY','S2_ATTACHED_NO_C','S3_PARTLY_UNRESOLVED']
fig,axs=plt.subplots(1,2,figsize=(9,4),layout='constrained')
for s,l,c,offset in [(S[1],LAB[1],COL[1],-.1),(S[2],LAB[2],COL[2],.1)]:
 vals=[]
 for tier in tiers:
  group=gg[(gg.condition=='corrected_baseline')&(gg.group==tier)]
  aa=group[group.strategy==s].set_index('realization_id').mean_normalized_burden_hr
  bb=group[group.strategy==S[0]].set_index('realization_id').mean_normalized_burden_hr
  vals.append((aa-bb).mean())
 axs[0].bar(np.arange(3)+offset,vals,width=.2,label=l,color=c)
axs[0].axhline(0,color='#999999',lw=.8);axs[0].set(xticks=range(3),xticklabels=['A only','A/B no C','Partial C'],ylabel='Mean burden difference from HF (h)',title='A  Evidence strata are not interchangeable');axs[0].legend(fontsize=8)
for k,m in enumerate(['population_normalized_burden_hr','population_resolved_mass_burden_hr']):
 axs[1].bar(np.arange(4)+(k-.5)*.3,[mean('corrected_baseline',s,m) for s in S],width=.3,label=['Full-population weighting','Population x resolved-mass weighting'][k],color=['#507d9a','#a6bccb'][k])
axs[1].set(xticks=range(4),xticklabels=['HF','Balanced','HospFirst','Efficiency'],ylabel='Mean burden (h)',title='B  Different population estimands');axs[1].legend(fontsize=7,loc='upper left')
save(fig,'Figure_S2_Denominators_and_coverage')
print('Created 6 figures from retained tables; no simulation or search called.')
