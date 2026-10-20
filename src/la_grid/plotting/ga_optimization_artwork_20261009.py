"""Read-only artwork for the bounded GA optimization diagnostic."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT as DATA
from la_grid.plotting.apply_coauthor_figure_feedback import COLORS,LABEL
from la_grid.plotting.selected_strategy_panels import ORDER,CORE,SUITE,all_summary
OUT=R/'results/figure_review/Additional_Evidence/GA_Optimization_20261009'
MM=72/25.4
plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],'font.size':7.5,'axes.titlesize':9.5,'axes.titleweight':'bold','axes.labelsize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,'axes.linewidth':.6,'pdf.fonttype':42,'figure.facecolor':'white','savefig.facecolor':'white'})
COL=['#527f9b','#b56e32','#557f65','#865d85'];GA_COL=['#426985','#805b7d','#4d8b91'];records=[];captions={}


def tidy(ax):
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#e6e6e6',lw=.4);ax.set_axisbelow(True)


def emit(fig,name,caption,sources):
    OUT.mkdir(parents=True,exist_ok=True);pdf=OUT/(name+'.pdf');fig.savefig(pdf);fig.savefig(OUT/(name+'.png'),dpi=600);plt.close(fig)
    with fitz.open(pdf) as doc:
        p=doc[0];spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']];minimum=min(s['size'] for s in spans);assert minimum>=6.99,(name,minimum);assert all('Arial' in s['font'] for s in spans),(name,'font');assert all(p.rect.contains(fitz.Rect(s['bbox'])) for s in spans),(name,'clipped')
        fonts=sorted(set(s['font'] for s in spans));height=p.rect.height/MM;records.append(dict(figure=name,width_mm=p.rect.width/MM,height_mm=height,min_font_pt=minimum,fonts=fonts,pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),scientific_sources=sources,formal_figure_replaced=False))
        preview=fitz.open();page=preview.new_page(width=210*MM,height=297*MM);rect=fitz.Rect(12.5*MM,15*MM,197.5*MM,(15+height)*MM);page.show_pdf_page(rect,doc,0);preview.save(OUT/(name+'_Page_Preview.pdf'));p.get_pixmap(matrix=fitz.Matrix(1.8,1.8)).save(OUT/(name+'_Review.png'))
    captions[name]=caption


def axes4(height=180):
    fig,axs=plt.subplots(2,2,figsize=(185/25.4,height/25.4));fig.subplots_adjust(left=.13,right=.975,bottom=.1,top=.94,wspace=.43,hspace=.68);return fig,axs


def final_groups():
    choice=json.loads((DATA/'SHORTLIST_SELECTION.json').read_text())['config_ids'];tuned=next(c for c in choice if c!='original_p100' and 'quality' not in c);warm=next((c for c in choice if 'quality' in c),choice[-1]);return tuned,warm


def convergence(ax,cid,label,color,coordinate='unique_candidates_evaluated',phase='shortlist'):
    folders=sorted((DATA/phase).glob(cid+'_s*'));observations=[]
    for folder in folders:
        if coordinate=='generation':
            q=pd.read_csv(folder/'GENERATION_DIAGNOSTICS.csv');x=q.generation.to_numpy();y=q.best_observed_service_loss_hr.to_numpy();initial_index=0
        else:
            with np.load(folder/'CANDIDATES.npz') as z:
                y=np.minimum.accumulate(-z['fitness']);x=np.arange(1,len(y)+1) if coordinate=='unique_candidates_evaluated' else z['first_attempt' if coordinate=='total_attempts' else 'first_elapsed_seconds'];initial_index=int(np.flatnonzero(z['first_generation']==0)[-1])
        observations.append((x[initial_index:],y[initial_index:]))
    upper=min(x[-1] for x,y in observations);lower=max(x[0] for x,y in observations);xgrid=np.linspace(lower,upper,101);curves=[]
    for x,y in observations:
        ix=np.clip(np.searchsorted(x,xgrid,side='right')-1,0,len(y)-1);curves.append(y[ix])
    v=np.array(curves);med=np.median(v,axis=0);lo,hi=np.quantile(v,[.05,.95],axis=0);ax.step(xgrid,med,where='post',color=color,lw=1.2,label=label);ax.fill_between(xgrid,lo,hi,step='post',color=color,alpha=.12,lw=0)


def s05():
    tuned,warm=final_groups();d=pd.read_csv(DATA/'GA_PARAMETER_SENSITIVITY.csv');q=d[d.phase.isin(['shortlist','operator_confirmation'])];best=q.groupby(['phase','config_id']).best_planning_loss_hr.mean().sort_values().index[0];fig,axs=axes4(190);a,b,c,e=axs.flat
    for cid,label,color in [('original_p100','Original GA',COL[0]),(tuned,'Tuned, legacy start',COL[1]),(best[1],'Tuned variant, warm start',COL[2])]:convergence(a,cid,label,color,phase=best[0] if cid==best[1] else 'shortlist')
    a.axhline(33.57830256,color='black',ls='--',lw=.7,label='Impact-first: 33.578303 h');a.axhline(33.038131743,color='#666666',ls=':',lw=.7,label='Previous best: 33.038132 h');a.axhline(32.997840773882714,color='#444444',ls='-.',lw=.5,label='New best: 32.997841 h');a.set_xlabel('Distinct objective evaluations');a.ticklabel_format(axis='x',style='sci',scilimits=(3,3));a.set_ylabel('Planning service loss (h)');a.set_title('A. Equal-budget search progress');a.legend(loc='upper right',frameon=True,edgecolor='none',facecolor='white',framealpha=1,fontsize=7,columnspacing=.5,handlelength=1.5)
    screen=d[d.phase.eq('screen')];x=np.arange(3)
    for offset,p,color in [(-.12,100,COL[0]),(.12,500,COL[1])]:
        vals=[];ranges=[]
        for elites in [0,1,3]:
            cid=f'original_p{p}' if elites==0 else f'p{p}_e{elites}';v=screen[screen.config_id.eq(cid)].best_planning_loss_hr.to_numpy();vals.append(v.mean());ranges.append([v.mean()-v.min(),v.max()-v.mean()])
        b.errorbar(x+offset,vals,yerr=np.array(ranges).T,color=color,fmt='o-',ms=3,lw=1,capsize=2,label=f'Population {p}')
    b.set_xticks(x,['Archive only','One elite','Three elites']);b.set_ylabel('Planning service loss (h)');b.set_title('B. Survival and population interact');b.legend(frameon=False,fontsize=7.5);b.text(.98,.04,'50,000 distinct evaluations',ha='right',transform=b.transAxes,fontsize=7)
    groups=[d[(d.phase.eq('shortlist'))&d.config_id.eq('original_p100')].best_planning_loss_hr.to_numpy(),d[d.phase.eq(best[0])&d.config_id.eq(best[1])].best_planning_loss_hr.to_numpy()]
    local=json.loads((DATA/'local_search/previous_best/ACCEPTED_MOVES.json').read_text());local100=next(z['after_service_loss_hr'] for z in local if z['distinct_evaluations']==100000);groups.append(np.array([local100]));hybrid=[json.loads(p.read_text())['best_planning_loss_hr'] for p in (DATA/'hybrid').glob('*/RUN.json')];groups.append(np.array(hybrid))
    for j,v in enumerate(groups):c.scatter(j+np.linspace(-.1,.1,len(v)),v,s=10,color=COL[j],edgecolors='none',alpha=.7);c.plot([j-.18,j+.18],[np.median(v)]*2,color=COL[j],lw=1.4)
    c.axhline(33.038131743,color='#444444',ls=':',lw=.7);c.set_xticks(range(4),['Original','Tuned\nwarm start','Local\nrefinement','Hybrid']);c.set_ylabel('Planning service loss (h)');c.set_title('C. Search methods at 100,000-query budget',pad=26);c.text(.98,.98,'Local: one deterministic path',ha='right',va='top',transform=c.transAxes,fontsize=7)
    effects=pd.read_csv(DATA/'reused_evaluation/OUTCOME_COMPARISONS.csv');selected=json.loads((DATA/'reused_evaluation/CANDIDATE_SELECTION.json').read_text())['candidates'];fields=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr'];labels=['All tracts','Q4 tracts','Hospital-linked\ntracts']
    for j,record in enumerate(selected):
        for i,f in enumerate(fields):
            q=effects[effects.candidate.eq(record['candidate_id'])&effects.reference.eq('impact-first')&effects.source_field.eq(f)].iloc[0];e.errorbar(q.mean_change,i+(j-1)*.16,xerr=[[q.mean_change-q.bootstrap_mean_ci95_low],[q.bootstrap_mean_ci95_high-q.mean_change]],fmt=['o','s','D'][j],color=GA_COL[j],ms=3,lw=.8,capsize=1.5,label=f'Candidate {j+1}' if i==0 else None)
    e.axvline(0,color='#444444',lw=.6);e.set_yticks(range(3),labels);e.set_ylim(2.5,-.5);e.set_xlabel('Service-loss change from Impact-first (h)',fontsize=7.5);e.set_title('D. Reused-cohort outcomes',pad=26);e.legend(frameon=False,loc='lower center',bbox_to_anchor=(.5,1.015),fontsize=7,ncol=3,columnspacing=.5,handletextpad=.3,handlelength=1)
    for ax in axs.flat:tidy(ax)
    emit(fig,'FigS05_Optimization_Candidate','Genetic algorithm (GA) optimization and exploratory evaluation. A: medians and 5th-95th seed ranges across twenty independent searches on the unchanged 64-realization planning objective; these ranges are not confidence intervals. Each run uses a fresh exact-permutation cache and equal distinct-evaluation budgets. Curves begin after initial-population scoring; reference and initialization queries remain included in the budget. The warm start explicitly includes the previous best sequence; its initial advantage is not newly discovered improvement. B: means and min-max across five seeds at 50,000 distinct evaluations; the independent archive is preserved in all variants, while elitism changes survival in the evolving population. C: final results at 100,000 joint distinct queries; short horizontal lines are medians, points are seeds. Local search is one deterministic path from the previous best. Hybrid uses a 50,000-query GA prefix and local refinement through a shared cache to a 100,000-query total. Different initialization is stated rather than presented as an operator-only comparison. D: three sequences chosen solely by planning loss and hashed before reusing the previously inspected 1,000 2pc50/C57/D1 evaluation realizations. Points are mean differences from Impact-first; whiskers are realization-bootstrap 95% confidence intervals for the mean (10,000 resamples). All-tract and Q4 loss are population-weighted; hospital-linked loss is an equal-tract mean. Evaluation integrates 0-480 h. Reuse is exploratory, not an untouched test. Formal strategies and artwork remain separate. Reference values are Impact-first33.578303 h, previous planning best33.038132 h and best found in this study32.997841 h. Neither flat archives nor finite search certify global optimality.',['GA_PARAMETER_SENSITIVITY.csv','SHORTLIST_SELECTION.json','GA_LOCAL_SEARCH_AND_HYBRID_RESULTS.csv','reused_evaluation/OUTCOME_COMPARISONS.csv'])


def sensitivity():
    d=pd.read_csv(DATA/'GA_PARAMETER_SENSITIVITY.csv');d=d[d.phase.eq('screen')];fig,axs=axes4(185)
    for ax,factor,vals,title in [(axs[0,0],'mutation',[.05,.1,.2,.4,.6],'A. Mutation by population'),(axs[0,1],'tournament',[2,3,5],'B. Selection by population'),(axs[1,0],'elites',[0,1,3],'C. Survival by population')]:
        for p,col in [(100,COL[0]),(500,COL[1])]:
            means=[];std=[]
            for value in vals:
                cid=f'original_p{p}' if value==dict(mutation=.2,tournament=3,elites=0)[factor] else f'p{p}_'+dict(mutation='m',tournament='k',elites='e')[factor]+f'{value:g}'
                q=d[d.config_id.eq(cid)].best_planning_loss_hr;means.append(q.mean());std.append(q.std())
            ax.errorbar(vals,means,yerr=std,fmt='o-',color=col,lw=1,ms=3,capsize=2,label=f'Population {p}')
        ax.set_xticks(vals,[f'{v:g}' for v in vals]);ax.set_xlabel(dict(mutation='Mutation probability',tournament='Tournament size',elites='Elites in evolving population')[factor]);ax.set_ylabel('Planning service loss (h)');ax.set_title(title);ax.legend(frameon=False);tidy(ax)
    ax=axs[1,1]
    for m,col in [(.1,COL[0]),(.4,COL[1])]:
        means=[];sd=[]
        for c in [.6,.8,.95]:
            cid=f'p100_m{m:g}' if c==.8 else f'p100_c{c:g}_m{m:g}';q=d[d.config_id.eq(cid)].best_planning_loss_hr;means.append(q.mean());sd.append(q.std())
        ax.errorbar([.6,.8,.95],means,yerr=sd,fmt='o-',ms=3,lw=1,capsize=2,color=col,label=f'Mutation {m:g}')
    ax.set_xticks([.6,.8,.95]);ax.set_xlabel('Crossover probability');ax.set_ylabel('Planning service loss (h)');ax.set_title('D. Crossover and mutation interact');ax.legend(frameon=False);tidy(ax)
    emit(fig,'GA_Parameter_Interactions','Controlled parameter contrasts at 50,000 distinct objective evaluations per seed. Points show five-seed means; whiskers show across-seed standard deviations, not realization uncertainty. Connecting lines only organize tested parameter levels; no untested response is fitted. Other mechanisms remain legacy ordered crossover, inversion mutation and deterministic-incumbent initialization unless the named factor is changed. Population × mutation, population × tournament and population × elitism comparisons use the same seeds. Crossover × mutation uses population 100. The design is targeted, not a full factorial or a claim of globally optimal hyperparameters.',['GA_PARAMETER_SENSITIVITY.csv','CONTROLLED_FACTOR_EFFECTS.csv'])


def original_dynamics():
    fig,axs=axes4(175)
    for population,label,color in [(100,'Population 100',COL[0]),(500,'Population 500',COL[1])]:
        prefix='extended100' if population==100 else 'extended500';frames=[pd.read_csv(DATA/'original_behavior_replay'/f'{prefix}_s{seed}'/'GENERATION_DIAGNOSTICS.csv') for seed in range(42,47)];generation=frames[0].generation.to_numpy()
        for field,ls,quantity in [('population_best_service_loss_hr','-','Population best'),('best_so_far_service_loss_hr','--','Archive')]:
            values=np.array([q[field] for q in frames]);axs[0,0].plot(generation,np.median(values,axis=0),color=color,ls=ls,lw=1.1,label=label+', '+quantity)
        for ax,field,title,ylabel in [(axs[0,1],'unique_population','B. Population remains distinct','Distinct chromosomes / population'),(axs[1,0],'directed_adjacency_overlap','C. Ordering concentration','Shared directed-adjacency fraction'),(axs[1,1],'parent_selection_intensity','D. Observed selection differential','Standardized selection differential')]:
            values=np.array([q[field] for q in frames]);values=values/population if field=='unique_population' else values;valid=np.isfinite(values).any(axis=0);values=values[:,valid];g=generation[valid];median=np.nanmedian(values,axis=0);lo,hi=np.nanquantile(values,[.05,.95],axis=0);ax.plot(g,median,color=color,lw=1.1,label=label);ax.fill_between(g,lo,hi,color=color,alpha=.12,lw=0);ax.set_title(title);ax.set_ylabel(ylabel);ax.set_xlabel('Generation');tidy(ax)
    axs[0,0].set_title('A. Archive and evolving population differ');axs[0,0].set_ylabel('Planning service loss (h)');axs[0,0].set_xlabel('Generation');fig.legend(*axs[0,0].get_legend_handles_labels(),frameon=False,fontsize=7,ncol=2,loc='upper center',bbox_to_anchor=(.55,.995));fig.subplots_adjust(top=.86);tidy(axs[0,0]);axs[0,1].legend(frameon=False,fontsize=7.5);axs[1,0].set_ylim(0,1);axs[0,1].set_ylim(0,1.04)
    emit(fig,'GA_Original_Population_Dynamics','Observed original-operator dynamics from exact reproductions of the previously completed five-seed population100 and500,1,000-generation searches. A contrasts median population-best loss (solid) with the independently retained archive (dashed). B gives the fraction of distinct chromosomes in the evolving population, not unique expensive evaluations. C measures ordering concentration using shared directed adjacencies in sixteen deterministic pair probes per generation. D is the selected-parent fitness differential divided by current-population fitness SD; this standardized measure is not uniformly weaker in the larger population. B-D bands are5th-95th across-seed ranges, not physical-realization intervals. Cached scores are used only to reconstruct these original trajectories and verify behavior; replay time is not a performance benchmark. Strong archive preservation does not ensure survival in the reproductive population, and high permutation diversity does not guarantee fitness improvement.',['ORIGINAL_HISTORY_PARITY.json','ORIGINAL_SEARCH_DYNAMICS_SUMMARY.csv','original_behavior_replay/*/GENERATION_DIAGNOSTICS.csv'])


def budget_figure():
    tuned,warm=final_groups();fig,axs=axes4(185)
    for ax,col,title,xlab in [(axs[0,0],'unique_candidates_evaluated','A. Distinct expensive queries','Distinct objective evaluations'),(axs[0,1],'total_attempts','B. Attempted calls including duplicates','Attempted fitness calls'),(axs[1,0],'elapsed_seconds','C. Wall-clock search time','Elapsed search time (s)'),(axs[1,1],'generation','D. Completed generations','Generation')]:
        for cid,label,color,phase in [('original_p100','Original (5 seeds)',COL[0],'budget_extension'),(tuned,'Tuned legacy (20 seeds)',COL[1],'shortlist'),('operator_swap','Tuned swap, warm start (5 seeds)',COL[2],'budget_extension')]:convergence(ax,cid,label,color,col,phase=phase)
        ax.axhline(33.038131743,color='#444444',lw=.7,ls=':');
        if col=='unique_candidates_evaluated':ax.ticklabel_format(axis='x',style='sci',scilimits=(3,3),useMathText=False)
        ax.set_xlabel(xlab);ax.set_ylabel('Planning service loss (h)');ax.set_title(title);tidy(ax);ax.legend(frameon=False,fontsize=7)
    emit(fig,'GA_Convergence_and_Computation','Search progress on four accounting axes. Each band is the 5th-95th across-seed range and the line is the seed median; five original/swap searches continue to 500,000 distinct queries, whereas twenty legacy-tuned searches stop at 100,000; values use the latest completed observation, without interpolation of new objective values. The dotted line is the previous planning best. Attempted calls include cache hits, whereas distinct queries are unique expensive scores per run. Wall-clock values include Python instrumentation/checkpoint overhead on a concurrently used host and are not standalone hardware benchmarks. Warm starts include the previous best order.',['GA_DIVERSITY_AND_SELECTION_DIAGNOSTICS.csv','GA_COMPUTATIONAL_BUDGET_COMPARISON.csv'])


def operators():
    d=pd.read_csv(DATA/'GA_PARAMETER_SENSITIVITY.csv');q=d[d.phase.eq('operators')];names=['operator_inversion','operator_swap','operator_insertion','operator_mixed','operator_cycle','operator_pmx','operator_adaptive','operator_restart','operator_crowding'];fig,ax=plt.subplots(figsize=(185/25.4,95/25.4));fig.subplots_adjust(left=.11,right=.98,bottom=.24,top=.88)
    for i,name in enumerate(names):
        v=q[q.config_id.eq(name)].best_planning_loss_hr;ax.scatter(i+np.linspace(-.1,.1,len(v)),v,s=12,color=COL[0],edgecolor='none');ax.plot([i-.17,i+.17],[v.mean()]*2,color=COL[0],lw=1.3)
    ax.axhline(33.038131743,color='#444444',ls=':',lw=.7,label='Previous planning best');ax.set_xticks(range(len(names)),[s.replace('operator_','').capitalize() for s in names],rotation=25,ha='right');ax.set_ylabel('Planning service loss (h)');ax.set_title('Permutation-operator variants at 50,000 distinct evaluations');ax.legend(frameon=False);tidy(ax)
    emit(fig,'GA_Operator_Comparison','Five independent seeds per operator variant at 50,000 distinct objective evaluations using the planning-only selected parent configuration. Dots are individual searches; horizontal marks are means. Inversion/swap/insertion/mixed change mutation; cycle/PMX change crossover. Adaptive mutation, stagnation restarts and deterministic crowding are separate mechanisms. All use the same exact physical evaluator and 64 planning samples. Two shortlisted operator configurations are separately replicated with twenty seeds. High-quality initialization is common within this screen and contains the previous best, so absolute performance is not an initialization-controlled comparison against legacy GA.',['OPERATOR_SELECTION.json','GA_PARAMETER_SENSITIVITY.csv','OPERATOR_CONFIRMATION_SELECTION.json'])


def restoration():
    selected=json.loads((DATA/'reused_evaluation/CANDIDATE_SELECTION.json').read_text())['candidates'];candidate=selected[0];cid=candidate['candidate_id'];q=all_summary();q=q[q.hazard.eq('2pc50')&q.resource_scenario.eq('C57_D1')];curves=pd.read_csv(SUITE/'Stage 6 Output_expanded/ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv');curves=curves[curves.hazard.eq('2pc50')];ga=pd.read_csv(DATA/f'reused_evaluation/{cid}/CURVES.csv');ga_summary=pd.read_csv(DATA/f'reused_evaluation/{cid}/SUMMARY.csv');fig=plt.figure(figsize=(185/25.4,195/25.4));ax=fig.add_axes([.13,.57,.845,.32]);keys=ORDER
    handles=[]
    for k in keys:
        p=curves[curves.strategy_id.eq(k)&curves.time_hr.le(100)];assert not p.empty;ax.plot(p.time_hr,p.mean_population_availability_proxy,color=COLORS[k],lw=1.2 if k in CORE+['unconstrained'] else .75,ls='-',alpha=1 if k in CORE+['unconstrained'] else .7);handles.append(Line2D([0],[0],color=COLORS[k],lw=1.2,label=LABEL[k]))
    ax.plot(ga.time_hr,ga.population_service_availability,color='#426985',lw=1.3,ls='--');handles.append(Line2D([0],[0],color='#426985',lw=1.3,ls='--',label='Planning-selected GA candidate 1'));fig.legend(handles=handles,loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(.53,.995),fontsize=7.5,columnspacing=.8,handlelength=1.8);ax.set_xlim(0,100);ax.set_ylim(-.025,1.04);ax.set_xlabel('Time after earthquake (h)');ax.set_ylabel('Population-weighted service availability');ax.set_title('A. Recovery shape on the reused cohort');tidy(ax)
    bx=fig.add_axes([.235,.13,.49,.29]);tx=fig.add_axes([.805,.13,.17,.29]);fields=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr'];metriccolors=['#527f9b','#c48a43','#8a989f'];rows=keys+[cid]
    fig.text(.58,.478,'B. Community service loss and recovery time',ha='center',fontsize=9.5,fontweight='bold');fig.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(metriccolors,['All tracts','Q4 tracts','Hospital-linked tracts'])],loc='upper center',ncol=3,frameon=False,bbox_to_anchor=(.6,.46),fontsize=7.5,columnspacing=.7)
    for i,k in enumerate(rows):
        p=ga_summary if k==cid else q[q.strategy_id.eq(k)]
        for j,(f,color) in enumerate(zip(fields,metriccolors)):bx.barh(i+(j-1)*.22,p[f].mean(),height=.2,color=color,lw=.25,edgecolor='white')
        v=p.population_T80_hr.to_numpy();m=v.mean();lo,hi=np.quantile(v,[.05,.95]);tx.errorbar(m,i,xerr=[[m-lo],[hi-m]],fmt='o',ms=3,lw=.65,capsize=1.5,color=COLORS.get(k,'#426985'))
    bx.set_yticks(range(len(rows)),[LABEL.get(k,'GA candidate 1') for k in rows]);bx.set_xlabel('Modeled service loss (h)');bx.set_xlim(left=0);tx.set_yticks([]);tx.set_xlabel('Population T80 (h)',fontsize=7.5)
    for a in [bx,tx]:a.set_ylim(len(rows)-.5,-.5);tidy(a)
    emit(fig,'Restoration_With_GA_Review_Candidate','Restoration comparison candidate under 2pc50, reference crew availability and repair duration. Six selected scheduled policy comparators and Unconstrained remain fixed; a single order chosen by the predeclared lowest-planning-loss rule is added as a diagnostic comparator without formal promotion. A shows mean population-weighted service availability over 0-100 h. B shows mean 0-480 h service loss for all tracts (population-weighted), Q4 (population-weighted) and hospital-linked tracts (equal-tract mean); bars begin at zero. Population T80 is the time to 80% aggregate modeled availability, with mean and 5th-95th realization ranges, not confidence intervals. The new candidate uses the already inspected 1,000-realization cohort; this is exploratory reuse, not unbiased independent validation. No delivered MW or clinical service capacity is inferred.',['reused_evaluation/CANDIDATE_SELECTION.json',f'reused_evaluation/{cid}/CURVES.csv',f'reused_evaluation/{cid}/SUMMARY.csv','Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet','Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet','results/revised_suite/LA_Grid_Revised_Suite_20260925/Stage 6 Output_expanded/ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv'])


def mechanism():
    candidate=json.loads((DATA/'reused_evaluation/CANDIDATE_SELECTION.json').read_text())['candidates'][0];cid=candidate['candidate_id'];ga=pd.read_csv(DATA/f'reused_evaluation/{cid}/CURVES.csv');saved=pd.read_csv(R/'results/diagnostics/selected_strategy_20261008/STATION_FUNCTIONALITY_CURVES.csv');effects=pd.read_csv(DATA/'reused_evaluation/OUTCOME_COMPARISONS.csv');fig,axs=axes4(185)
    for ax,source_col,ga_col,title in [(axs[0,0],'raw_functionality','station_mean_f','A. Raw station functionality'),(axs[0,1],'source_connected_effective_functionality','station_mean_e','B. Source-connected station functionality')]:
        for k in ['impact-first','hospital-first','degree-first','betweenness-first']:
            p=saved[saved.policy.eq(k)];ax.plot(p.time_hr,p[source_col],color=COLORS[k],lw=1.1,label=LABEL[k])
        ax.plot(ga.time_hr,ga[ga_col],color='#426985',ls='--',lw=1.3,label='GA candidate 1');ax.set_xlim(0,100);ax.set_ylim(-.025,1.04);ax.set_xlabel('Time after earthquake (h)');ax.set_ylabel('Mean station functionality');ax.set_title(title);tidy(ax)
    fig.legend(handles=axs[0,0].get_legend_handles_labels()[0],labels=axs[0,0].get_legend_handles_labels()[1],loc='upper center',ncol=3,frameon=False,fontsize=7,bbox_to_anchor=(.55,1));fig.subplots_adjust(left=.155,top=.88)
    for ax,fields,labels,title in [(axs[1,0],['L_self_population_mass_weighted_hr','L_threshold_population_mass_weighted_hr','L_source_population_mass_weighted_hr'],['Substation damage','Threshold','Source path'],'C. Service-loss component changes'),(axs[1,1],['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr'],['All tracts','Q4 tracts','Hospital-linked tracts'],'D. Community-outcome changes')]:
        for j,ref in enumerate(['impact-first','hospital-first']):
            for i,f in enumerate(fields):
                z=effects[effects.candidate.eq(cid)&effects.reference.eq(ref)&effects.source_field.eq(f)].iloc[0];ax.errorbar(z.mean_change,i+(j-.5)*.15,xerr=[[z.mean_change-z.bootstrap_mean_ci95_low],[z.bootstrap_mean_ci95_high-z.mean_change]],fmt='s' if ref=='impact-first' else 'o',color=COLORS[ref],ms=3,lw=.75,capsize=1.5,label=LABEL[ref] if i==0 else None)
        ax.axvline(0,color='#444444',lw=.6);ax.set_yticks(range(3),labels);ax.set_ylim(2.5,-.5);ax.set_title(title,pad=26);ax.set_xlabel('GA candidate 1 change from reference (h)',fontsize=7.5);ax.legend(loc='lower center',bbox_to_anchor=(.5,1.015),frameon=False,fontsize=7,ncol=2,columnspacing=.7);tidy(ax)
    emit(fig,'GA_Network_Station_Community_Mechanism','Station/network/community mechanism companion to the optimization diagnostic, not a replacement for S04. A/B are station-equal-weight mean raw f and effective source-connected e=fFC on the saved 1,000-realization 2pc50/C57/D1 cohort; curves display 0-100 h and are not MW capacity. C integrates population-dependency-weighted component loss over 0-480 h: substation damage 1-f, functionality threshold f(1-F), and source path fF(1-C). D reports all-tract/Q4 population-weighted and hospital-linked equal-tract service-loss changes. Squares compare the planning-selected GA candidate with Impact-first; circles with Hospital-first. Points are means, whiskers realization-bootstrap 95% confidence intervals for means. Reused-cohort results are exploratory; station functionality and community loss can change differently because network connectivity and population dependency intervene. S04 retains its distinct static criticality/dynamic-LCC purpose.',['reused_evaluation/OUTCOME_COMPARISONS.csv',f'reused_evaluation/{cid}/CURVES.csv','results/diagnostics/selected_strategy_20261008/STATION_FUNCTIONALITY_CURVES.csv'])


def packet():
    result=fitz.open()
    for name,caption in captions.items():
        with fitz.open(OUT/(name+'_Page_Preview.pdf')) as page:result.insert_pdf(page)
        page=result.new_page(width=210*MM,height=297*MM)
        left=12.5*MM;right=197.5*MM
        assert page.insert_textbox(fitz.Rect(left,15*MM,right,35*MM),name.replace('_',' '),fontname='hebo',fontsize=10)>=0
        assert page.insert_textbox(fitz.Rect(left,38*MM,right,280*MM),caption,fontname='helv',fontsize=9.5,lineheight=1.4)>=0
    result.save(OUT/'GA_OPTIMIZATION_REVIEW_PACKET.pdf',garbage=4,deflate=True);result.close()
    (OUT/'CAPTIONS.md').write_text('\n\n'.join('## '+name+'\n\n'+caption for name,caption in captions.items())+'\n',encoding='utf-8')
    for record in records:
        source_hashes={}
        for pattern in record['scientific_sources']:
            candidates=list(DATA.glob(pattern)) if not (R/pattern).exists() else [R/pattern]
            for source in candidates:
                if source.is_file():
                    with source.open('rb') as stream:source_hashes[source.relative_to(R).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
        assert source_hashes,record['figure']
        record['source_files_sha256']=source_hashes
        with fitz.open(OUT/(record['figure']+'.pdf')) as doc:
            record['all_font_resources']=[list(x) for x in doc.get_page_fonts(0)]
            strokes=[d['width'] for d in doc[0].get_drawings() if d.get('type') in ['s','fs'] and d.get('width',0)>0]
            record['minimum_positive_stroke_pt']=min(strokes)
            record['maximum_stroke_pt']=max(strokes)
            assert record['minimum_positive_stroke_pt']>=.1 and record['maximum_stroke_pt']<=1.5
        record['png_sha256']=hashlib.sha256((OUT/(record['figure']+'.png')).read_bytes()).hexdigest()
        record['png_dpi']=600
        with fitz.open(OUT/(record['figure']+'_Page_Preview.pdf')) as preview:preview[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(OUT/(record['figure']+'_Page_Preview.png'))
    (OUT/'ARTWORK_AUDIT.json').write_text(json.dumps(records,indent=2)+'\n')
    pd.DataFrame([{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in records]).to_csv(OUT/'FIGURE_INDEX.csv',index=False)

if __name__=='__main__':s05();sensitivity();original_dynamics();budget_figure();operators();restoration();mechanism();packet();print('ARTWORK COMPLETE',len(records))
