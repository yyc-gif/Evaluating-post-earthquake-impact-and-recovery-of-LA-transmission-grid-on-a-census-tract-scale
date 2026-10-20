"""Apply the 2026-10-08 co-author presentation comments to stored figures.

All scientific tables are read-only. No trajectories, uncertainty estimation,
models or scientific execution stages are invoked. Original artwork remains
recoverable at BASE_COMMIT; only current display files and indexes are updated.
"""
from pathlib import Path
import csv, hashlib, json, re, shutil, subprocess, tempfile
import fitz
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from la_grid.paths import REPO_ROOT
from la_grid.plotting.apply_outcome_display_feedback import fonts, sha, text, update_csv
from la_grid.plotting.apply_map_metric_identity_feedback import CLUSTER_COLORS, packets

ROOT=REPO_ROOT
REVIEW=ROOT/'results/figure_review'
BASE_COMMIT='8b0b75397a1a6dc152fde95289696ae63d71087d'
TEMP=Path(tempfile.gettempdir())/'la_coauthor_figures_20261008'
MM=72/25.4
ORDER=['impact-first','hospital-first','degree-first','vulnerability-first',
       'centrality-first','betweenness-first','closeness-first','random','unconstrained']
LABEL={k:k.replace('-first','-first').capitalize() for k in ORDER}
COLORS={'impact-first':'#ff7f00','hospital-first':'#555555','degree-first':'#4daf4a',
        'vulnerability-first':'#a65628','centrality-first':'#e41a1c',
        'betweenness-first':'#b59a00','closeness-first':'#377eb8',
        'random':'#9a9a9a','unconstrained':'#000000'}
CORE=set(ORDER[:4]+['unconstrained'])
plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],'font.size':7.5,
    'axes.titlesize':9.5,'axes.titleweight':'bold','axes.labelsize':8.5,
    'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,
    'axes.linewidth':.6,'pdf.fonttype':42,'figure.facecolor':'white'})


def baseline(key):
    """Read precise baseline LFS bytes without checking out or resetting files."""
    path='results/figure_review/'+key+'.pdf'
    raw=subprocess.check_output(['git','show',BASE_COMMIT+':'+path],cwd=ROOT)
    if raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
        oid=re.search(rb'oid sha256:([0-9a-f]{64})',raw).group(1).decode()
        common=Path(subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip())
        if not common.is_absolute():common=ROOT/common
        cache=TEMP/(key.replace('/','_')+'_baseline.pdf')
        obj=common/'lfs/objects'/oid[:2]/oid[2:4]/oid
        candidate=cache if cache.exists() else (obj if obj.exists() else ROOT/path)
        raw=candidate.read_bytes()
        if not cache.exists():cache.write_bytes(raw)
        assert hashlib.sha256(raw).hexdigest()==oid
    assert raw.startswith(b'%PDF')
    return fitz.open(stream=raw,filetype='pdf'),hashlib.sha256(raw).hexdigest()


def baseline_digest(path):
    raw=subprocess.check_output(['git','show',BASE_COMMIT+':'+path],cwd=ROOT)
    if raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
        return re.search(rb'oid sha256:([0-9a-f]{64})',raw).group(1).decode()
    return hashlib.sha256(raw).hexdigest()


def finish(doc,key,details):
    path=REVIEW/(key+'.pdf');tmp=path.with_suffix('.coauthor.pdf')
    doc.save(tmp,garbage=4,deflate=True);doc.close();tmp.replace(path)
    with fitz.open(path) as d:
        p=d[0];spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
        minimum=min(s['size'] for s in spans)
        assert minimum>=6.99,(key,minimum)
        assert all('Arial' in s['font'] for s in spans)
        assert all(p.rect.contains(fitz.Rect(s['bbox'])) for s in spans),(key,'clipped text')
        pix=p.get_pixmap(matrix=fitz.Matrix(600/72,600/72),alpha=False)
        pix.set_dpi(600,600);pix.save(path.with_suffix('.png'))
        p.get_pixmap(matrix=fitz.Matrix(1.8,1.8)).save(TEMP/(path.stem+'_after.png'))
        details.update(file=key+'.pdf',size_mm=[p.rect.width/MM,p.rect.height/MM],
            min_font_pt=minimum,pdf_sha256=sha(path),png_sha256=sha(path.with_suffix('.png')))
    return details


def eval_summary():
    paths=[ROOT/'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',
           ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet']
    full=pd.concat([pd.read_parquet(p) for p in paths],ignore_index=True)
    data=full[full.hazard.eq('2pc50') & full.resource_scenario.eq('C57_D1') &
              full.mapping.eq('M1_UTILITY_003') & full.gate.eq('G1_BASELINE_050') &
              full.strategy_id.isin(ORDER)].copy()
    assert data.groupby('strategy_id').size().to_dict()=={k:1000 for k in ORDER}
    return data,[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths]


def fig04(data,sources):
    key='Main/Fig04';doc,before=baseline(key);p=doc[0]
    # A's curves, coordinates and policy paint are preserved. Change only key.
    p.add_redact_annot(fitz.Rect(25*MM,90*MM,185*MM,112*MM),fill=(1,1,1))
    p.add_redact_annot(fitz.Rect(0,115*MM,185*MM,p.rect.height),fill=(1,1,1))
    p.apply_redactions(images=2,graphics=2,text=0);fonts(p)
    groups=[(35,'Infrastructure-based',['degree-first','centrality-first','betweenness-first','closeness-first']),
            (95,'Community / equity-informed',['impact-first','hospital-first','vulnerability-first']),
            (156,'Baselines',['unconstrained','random'])]
    for x,title,keys in groups:
        text(p,x,92.5,title,7.5,True)
        for i,k in enumerate(keys):
            color=tuple(int(COLORS[k][j:j+2],16)/255 for j in [1,3,5])
            if k not in CORE:color=tuple(.45*c+.55 for c in color)
            y=97+i*4
            p.draw_line((x*MM,(y-1)*MM),((x+6)*MM,(y-1)*MM),color=color,width=1.2 if k in CORE else .7)
            text(p,x+8,y,LABEL[k],7.5,k in CORE)
    metrics=[('population_weighted_normalized_burden_hr','All-tract','#497f9b'),
             ('burden_Q4_hr','Q4 tract','#c48a43'),
             ('hospital_mean_normalized_burden_hr','Hospital-tract','#8a989f')]
    fig=plt.figure(figsize=(185/25.4,90/25.4))
    fig.text(.5,.965,'B. Service loss and recovery time',ha='center',va='top',fontsize=9.5,fontweight='bold')
    fig.text(.5,.895,'Means and 5th-95th realization ranges',ha='center',va='top',fontsize=7.5)
    fig.legend(handles=[Patch(facecolor=c,label=l+' service loss') for _,l,c in metrics],
        loc='upper center',bbox_to_anchor=(.5,.845),ncol=3,frameon=False,
        handlelength=1.1,handleheight=.7,handletextpad=.4,columnspacing=1.0)
    ax=fig.add_axes([.195,.17,.49,.575]);t=fig.add_axes([.78,.17,.19,.575])
    rows=[]
    for i,k in enumerate(ORDER):
        q=data[data.strategy_id.eq(k)];alpha=1 if k in CORE else .48
        for j,(metric,label,color) in enumerate(metrics):
            values=q[metric].to_numpy(float);mean=values.mean();lo,hi=np.quantile(values,[.05,.95]);y=i+(j-1)*.22
            ax.barh(y,mean,height=.20,color=color,edgecolor='white',lw=.25,alpha=alpha,zorder=2)
            ax.errorbar(mean,y,xerr=[[mean-lo],[hi-mean]],fmt='none',ecolor='#303030',
                elinewidth=.6 if k in CORE else .45,capsize=1.5,alpha=alpha,zorder=3)
            rows.append({'strategy':k,'metric':metric,'mean':float(mean),'p05':float(lo),'p95':float(hi)})
        values=q.population_T80_hr.to_numpy(float);mean=values.mean();lo,hi=np.quantile(values,[.05,.95])
        t.errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt='o',ms=3 if k in CORE else 2,
            color=COLORS[k],alpha=alpha,lw=.7,capsize=1.5)
        rows.append({'strategy':k,'metric':'population_T80_hr','mean':float(mean),'p05':float(lo),'p95':float(hi)})
    ax.set_yticks(range(9),[LABEL[k] for k in ORDER]);ax.tick_params(axis='y',length=0,pad=4)
    for k,l in zip(ORDER,ax.get_yticklabels()):l.set_fontweight('bold' if k in CORE else 'normal')
    for a in [ax,t]:
        a.set_ylim(8.5,-.5);a.spines[['top','right']].set_visible(False);a.grid(axis='x',color='#e4e4e4',lw=.4,zorder=0)
    ax.set_xlim(0,50);ax.set_xlabel('Service loss (h)')
    t.set_yticks([]);t.set_xlim(35,62);t.set_xticks([40,50,60]);t.set_xlabel('Population T80 (h)',fontsize=7.5)
    temp=TEMP/'Fig04_grouped_outcomes.pdf';fig.savefig(temp);plt.close(fig)
    with fitz.open(temp) as overlay:p.show_pdf_page(fitz.Rect(0,115*MM,185*MM,205*MM),overlay,0)
    return finish(doc,key,{'before_sha256':before,'change':'Mechanism-grouped key; three grouped service-loss bars per strategy with preserved realization ranges; T80 remains separate.',
        'scientific_sources':sources,'display_values':rows,'curve_geometry_changed':False})


def fig05():
    key='Main/Fig05';doc,before=baseline(key);p=doc[0];fonts(p)
    drawings=[d for d in p.get_drawings() if d['fill'] and
        max(abs(d['fill'][i]-v) for i,v in enumerate((.65098,.33725,.15686)))<.002 and
        80<d['rect'].y0<210 and d['rect'].x1<270]
    assert len(drawings)==1,len(drawings)
    r=drawings[0]['rect'];target=(r.x0+r.x1)/2,(r.y0+r.y1)/2
    text(p,52,72.8,'Vulnerability-first',7.5,True,True)
    start=fitz.Point(52*MM,69.5*MM);end=fitz.Point(target[0]+3.3,target[1]+3.3)
    p.draw_line(start,end,color=(.25,.25,.25),width=.6)
    v=start-end;v=v/abs(v);normal=fitz.Point(-v.y,v.x)
    p.draw_polyline([end+v*3+normal*1.5,end,end+v*3-normal*1.5],color=(.25,.25,.25),width=.6)
    return finish(doc,key,{'before_sha256':before,'change':'A: directly label the existing Vulnerability-first point with an arrow.',
        'dot_center_pt':list(target),'data_coordinates_changed':False})


def s06():
    key='Supplement/FigS06';old,before=baseline(key)
    # Remove the repeated public-site benchmark. Keep full-size native panels.
    doc=fitz.open();p=doc.new_page(width=185*MM,height=152*MM)
    # No artwork downscaling: crop away only the now-inapplicable shared key.
    p.show_pdf_page(fitz.Rect(45*MM,0,132*MM,60*MM),old,0,clip=fitz.Rect(0,10*MM,87*MM,70*MM))
    p.show_pdf_page(fitz.Rect(0,67*MM,89*MM,152*MM),old,0,clip=fitz.Rect(0,72*MM,89*MM,157*MM))
    p.show_pdf_page(fitz.Rect(91*MM,67*MM,185*MM,152*MM),old,0,clip=fitz.Rect(91*MM,72*MM,185*MM,157*MM))
    spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
    changes=[]
    for s in spans:
        if s['text'].startswith('C. Service-requirement'):new=s['text'].replace('C.','B.',1)
        elif s['text'].startswith('D. Functionality-threshold'):new=s['text'].replace('D.','C.',1)
        else:continue
        changes.append((s,new));p.add_redact_annot(fitz.Rect(s['bbox']),fill=(1,1,1))
    p.apply_redactions(images=0,graphics=0,text=0);fonts(p)
    for s,new in changes:p.insert_text(s['origin'],new,fontname='DisplayArialBold',fontsize=s['size'])
    old.close()
    return finish(doc,key,{'before_sha256':before,'change':'Repeated public-site benchmark removed; unchanged native cutoff/gate/threshold panels reflowed and lettered A/B/C.',
        'benchmark_location':'Main/Fig02, Panel D','scientific_graphics_scaled':False})


def s09():
    key='Supplement/FigS09';doc,before=baseline(key);p=doc[0];fonts(p)
    # Replace only legend swatches, maintaining their location inside Panel A.
    p.add_redact_annot(fitz.Rect(77.1*MM,51.4*MM,80.8*MM,71.4*MM),fill=(1,1,1))
    p.apply_redactions(images=0,graphics=2,text=0);fonts(p)
    for i,color in enumerate(CLUSTER_COLORS.values()):
        rgb=tuple(int(color[j:j+2],16)/255 for j in [1,3,5]);y=(54+i*4)*MM
        p.draw_circle((79*MM,y-.6*MM),1.05*MM,color=(1,1,1),fill=rgb,width=.25)
    source=ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/pca_stats_with_eigenvalues.csv'
    stats=pd.read_csv(source);assert stats.Eigenvalue.gt(1).sum()==5
    # The PCA selection rule is eigenvalue > 1, not a demonstrated scree elbow.
    # Plot rectangle and saved ratio identify the existing PC5 point exactly.
    x0,x1=330.1242,492.0;y0,y1=45.2,211.05
    ratio=float(stats.loc[stats.PC.eq('PC5'),'Explained_Variance_Ratio'].iloc[0])
    # Recover the existing native circle center rather than estimating position.
    circles=[d for d in p.get_drawings() if d['fill'] and .15<d['fill'][0]<.4 and
        .3<d['fill'][1]<.6 and .35<d['fill'][2]<.8 and d['rect'].x0>330 and
        d['rect'].y0>45 and d['rect'].y1<212 and 2<d['rect'].width<7]
    by_x={}
    for item in circles:
        x=round(item['rect'].x0,2)
        if x not in by_x or item['rect'].y0>by_x[x]['rect'].y0:by_x[x]=item
    circles=list(by_x.values())
    circles=sorted(circles,key=lambda d:d['rect'].x0)
    assert len(circles)==11,len(circles)
    r=circles[4]['rect'];target=fitz.Point((r.x0+r.x1)/2,(r.y0+r.y1)/2)
    text(p,159,44.8,'Five PCs selected',7.5,True,True)
    start=fitz.Point(153*MM,46.0*MM);end=target+fitz.Point(3,-3)
    p.draw_line(start,end,color=(.25,.25,.25),width=.6)
    v=start-end;v=v/abs(v);normal=fitz.Point(-v.y,v.x)
    p.draw_polyline([end+v*3+normal*1.5,end,end+v*3-normal*1.5],color=(.25,.25,.25),width=.6)
    return finish(doc,key,{'before_sha256':before,'change':'Cluster legend circle diameter increased by 50%; annotate the selected fifth PC without relabeling it an elbow.',
        'pca_source':source.relative_to(ROOT).as_posix(),'pca_sha256':sha(source),
        'pc_selection_rule':'Five eigenvalues exceed 1; no new PCA or elbow computation.',
        'selected_pc5_ratio':ratio,'selected_pc5_center_pt':list(target)})


def s11():
    key='Supplement/FigS11';old,before=baseline(key)
    full=REVIEW/'Additional_Evidence/Cross_Hazard_Policy_Contrasts.pdf'
    old.close();shutil.copy2(TEMP/(key.replace('/','_')+'_baseline.pdf'),full)
    with fitz.open(full) as d:
        pix=d[0].get_pixmap(matrix=fitz.Matrix(600/72,600/72),alpha=False)
        pix.set_dpi(600,600);pix.save(full.with_suffix('.png'))
    source=ROOT/'provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv'
    effects=pd.read_csv(source)
    metrics=['population_weighted_normalized_burden_hr','burden_Q4_hr',
             'hospital_mean_normalized_burden_hr','population_T80_hr']
    labels=['All-tract\nservice loss','Q4 tract\nservice loss','Hospital-tract\nservice loss','Population\nT80']
    policies=ORDER[:-1]
    values=np.empty((8,4))
    for i,k in enumerate(policies):
        for j,m in enumerate(metrics):
            q=effects[effects.hazard.eq('2pc50') & effects.strategy_id.eq(k) & effects.metric.eq(m)]
            assert len(q)==1 and q.n_paired.iloc[0]==1000
            values[i,j]=q.mean_paired_difference.iloc[0]
    limit=float(np.abs(values).max())
    fig=plt.figure(figsize=(185/25.4,113/25.4));ax=fig.add_axes([.245,.185,.60,.685])
    cmap=plt.get_cmap('RdBu_r');im=ax.imshow(values,cmap=cmap,vmin=-limit,vmax=limit,aspect='auto')
    ax.set_xticks(range(4),labels);ax.set_yticks(range(8),[LABEL[k] for k in policies]);ax.tick_params(length=0,pad=5)
    ax.set_title('2pc50 policy changes relative to Unconstrained',pad=7)
    for i,k in enumerate(policies):
        ax.get_yticklabels()[i].set_fontweight('bold' if k in CORE else 'normal')
        for j in range(4):
            rgb=cmap((values[i,j]+limit)/(2*limit))[:3]
            lum=sum(w*c for w,c in zip([.2126,.7152,.0722],rgb))
            ax.text(j,i,f'{values[i,j]:+.2f}',ha='center',va='center',fontsize=7.5,color='white' if lum<.45 else '#15232a')
    cb=fig.colorbar(im,cax=fig.add_axes([.875,.185,.028,.685]));cb.set_label('Mean change (h)',fontsize=8.5);cb.ax.tick_params(labelsize=7.5)
    temp=TEMP/'S11_2pc50.pdf';fig.savefig(temp);plt.close(fig)
    record=finish(fitz.open(temp),key,{'before_sha256':before,'change':'One compact 2pc50 heatmap with four outcome columns; full cross-hazard evidence retained.',
        'scientific_source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),
        'metrics':metrics,'strategy_order':policies,'display_values':values.tolist(),
        'color_scale':'Common symmetric true-hour scale, not metric-specific normalized colors.',
        'cross_hazard_evidence':full.relative_to(ROOT).as_posix(),'cross_hazard_pdf_sha256':sha(full)})
    return record


def integrate(records,travel):
    changed={r['file']:r for r in records};generator=Path(__file__).relative_to(ROOT).as_posix()
    def idx(row):
        p=ROOT/row['source_path'];key=p.relative_to(REVIEW).with_suffix('.pdf').as_posix()
        if key in changed:
            shutil.copy2(p,ROOT/'results/figures'/row['file'])
            row.update(sha256_or_lfs_oid='sha256:'+sha(p),generator=generator,
                notes='Co-author presentation corrections: grouped outcome comparison, direct label, duplicate benchmark removal, PCA selection, compact 2pc50 evidence.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',idx)
    def manifest(row):
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key in changed:
            r=changed[key];p=REVIEW/row['final_name']
            row.update(source_file=p.relative_to(ROOT).as_posix(),current_source_file=p.relative_to(ROOT).as_posix(),
                source_commit='COAUTHOR_PRESENTATION_UPDATE_20261008',sha256=sha(p),
                parent_source_commit=BASE_COMMIT,parent_source_file=p.relative_to(ROOT).as_posix(),
                parent_sha256=baseline_digest('results/figure_review/'+row['final_name']),
                size_mm='%.3f x %.3f'%tuple(r['size_mm']),min_font_pt=f"{r['min_font_pt']:.3f}",status='COAUTHOR_PRESENTATION_UPDATE')
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    p=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';c=p.read_text(encoding='utf-8')
    blocks={}
    start=c.index('## Figure 4.');end=c.index('## Figure 5.',start)
    block=c[start:end]
    block=block.replace('Means and 5th–95th realization ranges for population-weighted modeled service loss, highest-vulnerability-quartile service loss, mean modeled service loss in hospital-linked tracts and population T80.',
        'Three grouped bars per policy show mean all-tract, Q4-tract and hospital-tract service loss; their whiskers show 5th–95th realization ranges. Population T80 is displayed separately with means and the same realization-range convention.')
    # Replace the precise B sentence if earlier wording differs.
    block=re.sub(r'\(B\).*?(?=\n\n|$)',
        '(B) Three grouped bars per policy show mean all-tract, Q4-tract and hospital-tract service loss; whiskers show 5th–95th realization ranges, not confidence intervals. All-tract and Q4 values use population weights within their respective domains; hospital-tract values are an equal-weight mean within hospital-linked tracts. Population T80 is shown separately as a mean and 5th–95th realization range, with a distinct time-to-threshold axis. Service loss integrates one minus modeled availability over 0–480 h, while the recovery curves display 0–100 h. Hospital-tract service loss does not measure hospital electricity delivery or clinical capacity. The grouped quantities share an hour unit but describe different tract populations and weighting definitions. Impact-first uses mapped population impact; Centrality-first uses network lambda2 impact. Infrastructure-based, community/equity-informed and baseline legend groups describe rule construction; they do not rank fairness or establish optimality.',block,flags=re.S)
    c=c[:start]+block+c[end:]
    start=c.index('## Supplementary Figure S6.');end=c.index('## Supplementary Figure S7.',start)
    heading='## Supplementary Figure S6. Dependency mapping and service-gate sensitivity\n\n'
    block=('Supplementary Figure S6 tests dependency and service-model assumptions. (A) Candidate-weight cutoff sensitivity relative to the 3% production cutoff, using the existing Hospital-first 2pc50 results. (B) Removal of both the station functionality threshold and source-connectivity requirement relative to the production service model. (C) Functionality thresholds 0.05 and 0.75 relative to the production value 0.50, with the same 14 Core sources. B/C display Impact-first, Hospital-first and Degree-first under 2pc50/C57_D1; Vulnerability-first was not evaluated for these service-gate cases. Points show mean distributional effects and lines show 5th–95th realization ranges, not confidence intervals. Service loss integrates one minus modeled service availability over 0–480 h. The public SCE assignment comparison on 337 comparable tracts is shown once in Figure 2D; it is public-record agreement/support, not feeder or service-territory ground truth.\n\n')
    c=c[:start]+heading+block+c[end:]
    start=c.index('## Supplementary Figure S9.');end=c.index('## Supplementary Figure S10.',start)
    block=c[start:end].rstrip()+' The marker at PC5 identifies the five components selected by eigenvalues greater than 1; it is not an independently established scree elbow. Cluster legend symbols belong to Panel A.\n\n'
    c=c[:start]+block+c[end:]
    start=c.index('## Supplementary Figure S11.');end=c.index('## Supplementary Figure S12.',start)
    block=('## Supplementary Figure S11. 2pc50 policy outcome contrasts\n\n'
        'Each cell is the saved mean distributional effect of the named scheduled policy relative to Unconstrained under 2pc50/C57_D1, using the same 1,000 physical realizations. Columns show all-tract service loss (population-weighted), Q4 tract service loss (population weights within the highest social-vulnerability quartile), hospital-tract service loss (equal-weight mean within hospital-linked tracts) and population T80. All loss integrals cover 0–480 h; T80 is the time to 80% modeled population-weighted service availability. The shared color scale and printed values are true hour differences, without per-metric rescaling. The source table includes 5th–95th realization-difference ranges; this mean heatmap does not display uncertainty. Hospital-tract service loss is not hospital electricity delivery or clinical capacity. Complete four-scenario contrasts remain in Additional Evidence: Cross_Hazard_Policy_Contrasts. Historical scenarios and 2pc50 use different fragility parameterizations, so those comparisons are not pure hazard-intensity sensitivity. Direct-community has the same sequence as Impact-first and is not listed separately.\n\n')
    c=c[:start]+block+c[end:]
    p.write_text(c,encoding='utf-8');packets(c)
    p=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';a=json.loads(p.read_text())
    a['current_code_files']=[x for x in a['current_code_files'] if x['path']!=generator]+[
        {'path':generator,'sha256':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'tracked_in_current_git':True}]
    p.write_text(json.dumps(a,indent=2)+'\n')
    (ROOT/'docs/reproducibility/COAUTHOR_FIGURE_FEEDBACK_20261008.json').write_text(json.dumps(
        {'base_commit':BASE_COMMIT,'figures':records,'directed_travel_review':travel,
         'scientific_stage_invoked':False,'source_tables_changed':False},indent=2)+'\n')
    p=REVIEW/'Additional_Evidence/README.md';body=p.read_text(encoding='utf-8')
    if '## Complete cross-hazard policy contrasts' not in body:
        body+='\n## Complete cross-hazard policy contrasts\n\n[Cross_Hazard_Policy_Contrasts.pdf](Cross_Hazard_Policy_Contrasts.pdf) retains the complete four-scenario policy evidence formerly shown in S11. The numbered S11 provides a compact 2pc50 view; no historical-scenario result was deleted. Refer to the S11 caption for the estimands and limits on cross-hazard interpretation.\n'
    p.write_text(body,encoding='utf-8')


def main():
    TEMP.mkdir(exist_ok=True)
    travel_path=ROOT/'data/travel/travel_task_to_task.csv'
    d=pd.read_csv(travel_path,index_col=0).to_numpy(float);delta=np.abs(d-d.T)
    travel={'file':travel_path.relative_to(ROOT).as_posix(),'sha256':sha(travel_path),
        'matrix_shape':list(d.shape),'asymmetric_directed_entries':int(np.count_nonzero(delta>1e-12)),
        'max_reverse_direction_difference_hr':float(delta.max()),
        'action':'Retain both triangles: opposite road directions are not duplicate entries.'}
    data,sources=eval_summary();records=[]
    for fn,args in [(fig04,(data,sources)),(fig05,()),(s06,()),(s09,()),(s11,())]:
        print('Applying',fn.__name__,flush=True);records.append(fn(*args))
    integrate(records,travel)
    print('Presentation complete; no scientific stage executed.',flush=True)

if __name__=='__main__':main()
