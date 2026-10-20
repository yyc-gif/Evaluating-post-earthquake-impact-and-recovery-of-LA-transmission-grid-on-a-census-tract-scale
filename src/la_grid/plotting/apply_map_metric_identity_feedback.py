"""Correct current map colors, restore the Degree comparison, and align labels.

Presentation only. Reads saved tract-effect summaries and GIS boundaries.
No simulation, trajectory integration, scheduling, clustering, or CI estimation.
Degree effects use the exact algebraic identity (V-H) - (D-H) = V-D on
the same 1,000 realizations. No scientific source file is written.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

import fitz
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.plotting.refine_policy_cluster_presentation import streams, RGB_PATTERN, rgb, near
from la_grid.plotting.apply_outcome_display_feedback import fonts, update_csv, sha

ROOT = REPO_ROOT
REVIEW = ROOT / 'results/figure_review'
HISTORY = ROOT / 'provenance/figure_review_history/map_metric_identity_before_20261007'
TEMP = Path(tempfile.gettempdir()) / 'la_map_identity_feedback_20261007'
MM = 72/25.4
ARIAL = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
OLD_COLORS = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854']
# Explicit cluster-ID colors: blue, orange, green, cyan, brick red. Gray is reserved for N/A.
CLUSTER_COLORS = {1:'#4f8fb7', 2:'#e19243', 3:'#6ca274', 4:'#68a9b5', 5:'#b45f50'}
MAP_COLORS = ['#2166ac', '#80b4d4', '#c4c4c4', '#f4ae62', '#d96518']
KEYS = ['Main/Fig01', 'Main/Fig04', 'Main/Fig05', 'Main/Fig06', 'Main/Fig07',
        'Supplement/FigS09', 'Supplement/FigS11', 'Supplement/FigS12', 'Supplement/FigS13']

def plain(text):
    return text.replace('\xad','-').replace('\xa0',' ').replace('–','-').replace('−','-')

def source(key):
    p = REVIEW / (key+'.pdf')
    old = HISTORY / (key+'.pdf')
    old.parent.mkdir(parents=True, exist_ok=True)
    for ext in ['.pdf','.png']:
        if not old.with_suffix(ext).exists():
            shutil.copy2(p.with_suffix(ext),old.with_suffix(ext))
    return p,old

def categorical_colors(doc):
    counts = [0]*5
    for x in streams(doc):
        raw = doc.xref_stream(x)
        def change(m):
            color = tuple(float(m.group(i)) for i in [1,2,3])
            for i,old in enumerate(OLD_COLORS):
                if near(color,rgb(old)):
                    counts[i]+=1
                    return (' '.join(f'{v:.7f}' for v in rgb(CLUSTER_COLORS[i+1]))+' '+m.group(4).decode()).encode()
            return m.group(0)
        replacement=RGB_PATTERN.sub(change,raw)
        if replacement!=raw: doc.update_stream(x,replacement)
    return counts

def metric_labels(doc,key):
    """Replace only the identified text spans, leaving graph vertices untouched."""
    p=doc[0]; edits=[]
    for b in p.get_text('dict')['blocks']:
        for line in b.get('lines',[]):
            for s in line['spans']:
                old=plain(s['text']);new=None
                if old.startswith(('A. Population-weighted service loss','B. Population-weighted service loss')):
                    new=old[:2]+' All-tract service loss'
                elif re.match(r'[A-H]\. Q4 population-weighted service loss',old):
                    new=old[:2]+' Q4 tract service loss'
                elif re.match(r'[A-H]\. Hospital-linked mean service loss',old):
                    new=old[:2]+' Hospital-tract service loss'
                elif re.match(r'[A-H]\. Population-weighted$',old):new=old[:2]+' All-tract'
                elif re.match(r'[A-H]\. Q4 population-weighted$',old):new=old[:2]+' Q4 tract'
                elif re.match(r'[A-H]\. Hospital-linked mean$',old):new=old[:2]+' Hospital-tract'
                elif old=='Population-weighted' and not (key=='Main/Fig04' and s['bbox'][1]>530 and s['bbox'][0]>400):
                    new='All-tract' if not (key=='Main/Fig05' and line['dir'][1]<-.5 and s['bbox'][0]>200) else 'Tract'
                elif old=='Q4 population-weighted':new='Q4 tract'
                elif old in ['Hospital-linked mean','Hospital-linked']:new='Hospital-tract'
                elif old=='mean service' and key=='Main/Fig04':new='service'
                elif old.startswith('Hospital-linked tract panels:'):new=old.replace('Hospital-linked tract panels:','Hospital-tract panels:')
                if new is not None and new!=old:edits.append((s,line,new))
    for s,line,new in edits:
        p.add_redact_annot(fitz.Rect(s['bbox']),fill=(1,1,1))
    if edits:p.apply_redactions(images=0,graphics=0,text=0)
    p.insert_font(fontname='MetricArial',fontfile=ARIAL)
    p.insert_font(fontname='MetricArialBold',fontfile=BOLD)
    for s,line,new in edits:
        bold='Bold' in s['font']; f=fitz.Font(fontfile=BOLD if bold else ARIAL)
        rotation=90 if line['dir'][1]<-.5 else 270 if line['dir'][1]>.5 else 0
        origin=fitz.Point(s['origin'])
        if rotation:
            center=(s['bbox'][1]+s['bbox'][3])/2
            origin.y=center+f.text_length(new,fontsize=s['size'])/2
        elif key=='Main/Fig05' and 315<s['bbox'][1]<410 and s['bbox'][2]<151:
            origin.x=s['bbox'][2]-f.text_length(new,fontsize=s['size'])
        else:origin.x=(s['bbox'][0]+s['bbox'][2]-f.text_length(new,fontsize=s['size']))/2
        color=tuple(((s['color']>>shift)&255)/255 for shift in [16,8,0])
        p.insert_text(origin,new,fontname='MetricArialBold' if bold else 'MetricArial',
                      fontsize=s['size'],rotate=rotation,color=color)
    return [{'old':plain(s['text']),'new':new} for s,line,new in edits]

def spatial_effects():
    vp=ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_TRACT_EFFECTS.parquet'
    dp=ROOT/'Formal_Experiment_20260923/Formal_Results/TRACT_PAIRED_EFFECTS.parquet'
    v=pd.read_parquet(vp);v=v[v.hazard.eq('2pc50')].copy()
    d=pd.read_parquet(dp);d=d[d.hazard.eq('2pc50') & d.resource_scenario.eq('C57_D1') &
                              d.strategy_id.eq('degree-first') & d.reference_strategy.eq('hospital-first')].copy()
    assert len(d)==2315 and d.valid_paired_realizations.eq(1000).all()
    arrays={}
    for ref in ['hospital-first','impact-first']:
        q=v[v.reference_strategy.eq(ref)].copy()
        assert len(q)==2315 and q.valid_realizations.eq(1000).all()
        arrays[ref]=q.set_index('tract_id').mean_paired_delta_burden_hr.sort_index()
    degree=d.set_index('tract_id').paired_mean_delta_burden_hr.sort_index()
    assert arrays['hospital-first'].index.equals(degree.index)
    arrays['degree-first']=arrays['hospital-first']-degree
    # Independent algebra check against the stored all-tract policy means.
    formal=pd.read_parquet(ROOT/'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet')
    vf=pd.read_parquet(ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet')
    def case(frame,policy):
        return frame[frame.hazard.eq('2pc50') & frame.resource_scenario.eq('C57_D1') &
            frame.strategy_id.eq(policy) & frame.mapping.eq('M1_UTILITY_003') & frame.gate.eq('G1_BASELINE_050')]
    a=case(vf,'vulnerability-first'); b=case(formal,'degree-first')
    assert len(a)==len(b)==1000
    pop=d.set_index('tract_id').population.reindex(degree.index)
    expected=a.population_weighted_normalized_burden_hr.mean()-b.population_weighted_normalized_burden_hr.mean()
    displayed=np.average(arrays['degree-first'],weights=pop)
    assert abs(expected-displayed)<1e-9,(expected,displayed)
    shapes=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp')
    shapes['tract_id']=shapes.GEOID.astype(str).str.zfill(11)
    shapes=shapes[shapes.tract_id.isin(degree.index.astype(str))].to_crs(epsg=3310)
    assert shapes.tract_id.nunique()==2315
    limit=float(max(np.abs(values).max() for values in arrays.values()))
    plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],'font.size':7.5,
        'pdf.fonttype':42,'axes.linewidth':.6,'figure.facecolor':'white','savefig.facecolor':'white'})
    fig=plt.figure(figsize=(185/25.4,74/25.4))
    cmap=LinearSegmentedColormap.from_list('service_loss_blue_orange',MAP_COLORS,N=256)
    norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit)
    bounds=shapes.total_bounds
    for i,(ref,label) in enumerate(zip(['hospital-first','impact-first','degree-first'],
                                      ['Hospital-first','Impact-first','Degree-first'])):
        ax=fig.add_axes([.012+i*.330,.23,.316,.65])
        frame=shapes.merge(arrays[ref].rename('display_effect'),left_on='tract_id',right_index=True,validate='one_to_one')
        assert len(frame)==2315 and frame.display_effect.notna().all()
        frame.plot(column='display_effect',ax=ax,cmap=cmap,norm=norm,linewidth=.055,edgecolor='#f2f2f2')
        ax.set_xlim(bounds[0],bounds[2]);ax.set_ylim(bounds[1],bounds[3]);ax.set_aspect('equal');ax.axis('off')
        ax.set_title('Compared with '+label,fontsize=7.5,pad=5)
    cax=fig.add_axes([.19,.14,.62,.035])
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal')
    cb.set_label('Tract service-loss change (h)',fontsize=7.5,labelpad=2)
    cb.ax.tick_params(labelsize=7.5,length=2,pad=2);cb.outline.set_linewidth(.5)
    path=TEMP/'spatial_effect_panel.pdf';fig.savefig(path);plt.close(fig)
    return path,{'saved_sources':[str(vp.relative_to(ROOT)),str(dp.relative_to(ROOT))],
        'domain_tracts':2315,'realizations':1000,'degree_formula':'(Vulnerability - Hospital) - (Degree - Hospital)',
        'degree_population_weighted_display_change_hr':float(displayed),'degree_source_summary_change_hr':float(expected),
        'common_color_range_hr':[-limit,limit],'colormap':MAP_COLORS}

def replace_maps(doc,panel):
    page=doc[0];rect=fitz.Rect(0,174*MM,page.rect.width,page.rect.height)
    page.add_redact_annot(rect,fill=(1,1,1))
    page.apply_redactions(images=2,graphics=2,text=0)
    with fitz.open(panel) as p:page.show_pdf_page(fitz.Rect(0,175*MM,185*MM,249*MM),p,0)

def export(doc,key,details):
    path=REVIEW/(key+'.pdf');temp=path.with_suffix('.update.pdf')
    doc.save(temp,garbage=4,deflate=True);doc.close();temp.replace(path)
    with fitz.open(path) as d:
        p=d[0];spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
        assert min(s['size'] for s in spans)>=6.99,(key,min(s['size'] for s in spans))
        assert all('Arial' in s['font'] for s in spans)
        pix=p.get_pixmap(matrix=fitz.Matrix(600/72,600/72),alpha=False);pix.set_dpi(600,600);pix.save(path.with_suffix('.png'))
        p.get_pixmap(matrix=fitz.Matrix(1.8,1.8)).save(TEMP/(Path(key).name+'_after.png'))
        details.update(file=key+'.pdf',size_mm=[p.rect.width/MM,p.rect.height/MM],min_font_pt=min(s['size'] for s in spans),
                       pdf_sha256=sha(path),png_sha256=sha(path.with_suffix('.png')))
    return details

def packets(captions):
    order=[f'Main/Fig{i:02}.pdf' for i in range(1,8)]+[f'Supplement/FigS{i:02}.pdf' for i in [1]+list(range(3,14))]
    for label,files in [('ALL_MAIN_FIGURES.pdf',order[:7]),('ALL_SUPPLEMENT_FIGURES.pdf',order[7:])]:
        book=fitz.open()
        for key in files:
            with fitz.open(REVIEW/key) as d:book.insert_pdf(d)
        book.save(REVIEW/label,garbage=4,deflate=True);book.close()
    headings=list(re.finditer(r'(?m)^## (.+)\n\n',captions));lookup={}
    for i,m in enumerate(headings):
        title=m.group(1);body=captions[m.end():headings[i+1].start() if i+1<len(headings) else len(captions)].strip()
        if title.startswith('Figure '):key=f'Main/Fig{int(title.split(".")[0].replace("Figure ","")):02}.pdf'
        elif title.startswith('Supplementary Figure S'):key=f'Supplement/FigS{int(title.split(".")[0].replace("Supplementary Figure S","")):02}.pdf'
        else:continue
        lookup[key]=(title,body)
    book=fitz.open()
    for key in order:
        with fitz.open(REVIEW/key) as d:book.insert_pdf(d)
        title,body=lookup[key];page=book.new_page(width=185*MM,height=350*MM);fonts(page)
        assert page.insert_textbox(fitz.Rect(14*MM,16*MM,171*MM,28*MM),title,fontname='DisplayArialBold',fontsize=9.5)>=0
        assert page.insert_textbox(fitz.Rect(14*MM,31*MM,171*MM,333*MM),body,fontname='DisplayArial',fontsize=9.2,lineheight=1.22)>=0
    assert len(book)==38
    book.save(REVIEW/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()

def integrate(records):
    changed={r['file']:r for r in records};generator=Path(__file__).relative_to(ROOT).as_posix()
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip()
    def index(row):
        p=ROOT/row['source_path'];key=p.relative_to(REVIEW).with_suffix('.pdf').as_posix()
        if key not in changed:return
        shutil.copy2(p,ROOT/'results/figures'/row['file'])
        row.update(sha256_or_lfs_oid='sha256:'+sha(p),generator=generator,
                   notes='Current author-requested parallel service-loss labels, three spatial references and explicit non-pink cluster palette.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    def manifest(row):
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key not in changed:return
        p=REVIEW/row['final_name'];old=HISTORY/row['final_name'];r=changed[key]
        row.update(source_commit='MAP_METRIC_IDENTITY_UPDATE_20261007',sha256=sha(p),
            parent_source_commit=head,parent_source_file=old.relative_to(ROOT).as_posix(),parent_sha256=sha(old),
            min_font_pt=f"{r['min_font_pt']:.3f}",status='AUTHOR_REQUESTED_CURRENT_DISPLAY')
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    p=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';c=p.read_text(encoding='utf-8')
    c=c.replace('(E) Continuous tract-level mean service-loss change under Vulnerability-first relative to Hospital-first and Impact-first.',
                '(E) Continuous tract-level mean service-loss change under Vulnerability-first relative to Hospital-first, Impact-first and Degree-first.')
    # Use the exact current E wording if it is split differently in an older caption.
    start=c.index('## Figure 5.');end=c.index('## Figure 6.',start)
    block=c[start:end]
    block=re.sub(r'\(E\).*?(?=\n\n|$)',
        '(E) Tract mean service-loss changes under Vulnerability-first compared with Hospital-first, Impact-first and Degree-first, using the same 1,000 2pc50 realizations at 57 crews and repair-duration multiplier 1.00. Negative values indicate lower service loss; positive values indicate higher service loss. All three maps use identical geographic extent and the same zero-centered blue–orange scale; gray denotes changes close to zero, not missing data. Degree-first spatial changes are obtained from the saved per-tract mean differences using (Vulnerability-first relative to Hospital-first) less (Degree-first relative to Hospital-first). Colors describe the mean effect across realizations, not statistical significance or the mean population benefiting within individual realizations. Service loss integrates one minus modeled service availability over 0–480 h. Hospital-tract service loss is an equal-weight tract mean, not hospital electricity delivery or clinical capacity. No one metric establishes a most-equitable policy.',block,flags=re.S)
    c=c[:start]+block+c[end:]
    definition=('Throughout Figures 4–6 and Supplementary Figures S11–S13, All-tract service loss is the population-weighted mean of tract service-loss integrals; Q4 tract service loss uses population weights within the highest social-vulnerability quartile; Hospital-tract service loss is the equal-weight mean of those integrals within hospital-linked tracts. These labels identify different tract populations, without changing their respective weighting definitions. All loss integrals cover 0–480 h. Hospital-tract service loss is not hospital electricity delivery or clinical capacity. ')
    pos=c.index('\n\n',c.index('## Figure 4.'))+2
    if definition not in c:c=c[:pos]+definition+c[pos:]
    c=c.replace('Hospital-linked mean service loss','Hospital-tract service loss')
    p.write_text(c,encoding='utf-8');packets(c)
    a=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';authority=json.loads(a.read_text())
    authority['current_code_files']=[r for r in authority['current_code_files'] if r['path']!=generator]+[
        {'path':generator,'sha256':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'tracked_in_current_git':True}]
    a.write_text(json.dumps(authority,indent=2)+'\n')
    (ROOT/'docs/reproducibility/MAP_METRIC_IDENTITY_FEEDBACK_20261007.json').write_text(json.dumps(
        {'base_commit':head,'records':records,'cluster_id_colors':CLUSTER_COLORS,'scientific_source_changed':False},indent=2)+'\n')

def main():
    TEMP.mkdir(exist_ok=True);panel,map_audit=spatial_effects();records=[]
    for key in KEYS:
        print('Updating',key,flush=True);target,old=source(key);doc=fitz.open(old);details={}
        if key in ['Main/Fig01','Main/Fig07','Supplement/FigS09']:
            details['cluster_color_operator_counts']=categorical_colors(doc)
        if key not in ['Main/Fig01','Main/Fig07','Supplement/FigS09']:
            details['text_changes']=metric_labels(doc,key)
        if key=='Main/Fig05':replace_maps(doc,panel);details['spatial_panel']=map_audit
        records.append(export(doc,key,details))
    integrate(records)
    print('Complete collection updated. No scientific stage invoked.',flush=True)

if __name__=='__main__':main()
