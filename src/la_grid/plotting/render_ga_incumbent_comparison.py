"""Render S05 from saved GA best-so-far histories and final planning scores.

Presentation only: no objective evaluation and no GA invocation. The archive
includes the initial deterministic incumbent; coincident traces stay coincident.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from la_grid.paths import REPO_ROOT
from la_grid.plotting import Project_Visualizer as july

ROOT=REPO_ROOT
REVIEW=ROOT/'results/figure_review'
SOURCE=ROOT/'Formal_Experiment_20260923/Stage 5 Output_expanded'
HISTORY=ROOT/'provenance/figure_review_history/ga_incumbent_before_20261007'
SEEDS=[42,43,44,45,46]
COLORS=['#366e9f','#cc641b','#00856a','#8165a5','#967539']
MARKERS=['o','s','^','D','P']
MM=72/25.4
ARIAL='C:/Windows/Fonts/arial.ttf'
BOLD='C:/Windows/Fonts/arialbd.ttf'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def render():
    inputs=[]
    def table(name):
        path=SOURCE/name;inputs.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
        return pd.read_csv(path)
    final=table('GA_FIVE_SEED_CONVERGENCE.csv').sort_values('seed')
    assert final.seed.tolist()==SEEDS and not final.search_improved_incumbent.any()
    incumbent=-float(final.incumbent_fitness.iloc[0])
    assert np.allclose(-final.incumbent_fitness,incumbent,atol=1e-12,rtol=0)
    rules=table('INCUMBENT_DIRECT_SCORES_2pc50.csv')
    assert len(rules)==7 and rules.loc[rules.planning_burden_hr.idxmin(),'rule']=='impact-first'
    assert abs(float(rules.loc[rules.rule.eq('impact-first'),'planning_burden_hr'].iloc[0])-incumbent)<1e-9
    histories=[]
    for seed in SEEDS:
        h=table(f'GA_HISTORY_2pc50_{seed}.csv')
        assert h.generation.tolist()==list(range(101)) and set(h.seed)=={seed}
        loss=-h.best_so_far.to_numpy()
        assert np.all(np.diff(loss)<=1e-12) and np.all(loss>=incumbent-1e-9)
        assert abs(loss[-1]+float(final.loc[final.seed.eq(seed),'fitness'].iloc[0]))<1e-12
        histories.append((h,loss))
    horizon_path=SOURCE/'PLANNING_HORIZON.json'
    horizon=json.loads(horizon_path.read_text(encoding='utf-8'))
    inputs.append({'path':horizon_path.relative_to(ROOT).as_posix(),'sha256':sha(horizon_path)})
    before=REVIEW/'Supplement/FigS05.pdf'
    (HISTORY/'Supplement').mkdir(parents=True,exist_ok=True)
    for suffix in ['.pdf','.png']:
        original=HISTORY/'Supplement'/('FigS05'+suffix)
        if not original.exists():shutil.copy2(before.with_suffix(suffix),original)
    july.apply_publication_style()
    plt.rcParams.update({'font.sans-serif':['Arial'],'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(185/25.4,90/25.4))
    fig.subplots_adjust(left=.115,right=.98,bottom=.19,top=.79,wspace=.52)
    for i,((history,loss),color,marker) in enumerate(zip(histories,COLORS,MARKERS)):
        axes[0].plot(history.generation,loss,color=color,lw=1.2,alpha=.85,zorder=2)
        # Sparse symbols sample the original trace at actual generations. No
        # horizontal/vertical perturbation is applied to the saved data.
        indices=[10+15*i]
        axes[0].plot(history.generation.iloc[indices],loss[indices],linestyle='none',
            marker=marker,ms=4.4,color=color,markeredgecolor='white',markeredgewidth=.45,zorder=4)
        value=-float(final.loc[final.seed.eq(SEEDS[i]),'fitness'].iloc[0])
        axes[1].plot(SEEDS[i],value,linestyle='none',marker=marker,ms=4.4,color=color,
            markeredgecolor='white',markeredgewidth=.45,zorder=4)
    for ax in axes:
        ax.axhline(incumbent,color='black',linestyle='--',lw=1.0,zorder=3)
        ax.set_ylabel('Planning cumulative\nservice loss (h)',fontsize=july.FS_LABEL)
        ax.set_ylim(33.0,34.2);ax.set_yticks([33.0,33.4,33.8,34.2])
        ax.grid(axis='y',color='#e5e5e5',lw=.4);ax.grid(False,axis='x')
        ax.tick_params(labelsize=july.FS_TICK)
    axes[0].set(xlim=(0,100),xticks=[0,20,40,60,80,100],xlabel='Generation')
    axes[1].set(xlim=(41.6,46.4),xticks=SEEDS,xlabel='Genetic algorithm seed')
    axes[0].set_title('A. Best-so-far planning loss',fontsize=july.FS_TITLE,fontweight='bold',pad=8)
    axes[1].set_title('B. Final best result by seed',fontsize=july.FS_TITLE,fontweight='bold',pad=8)
    axes[0].text(50,incumbent+.17,'All five traces coincide',ha='center',va='bottom',fontsize=7.5)
    axes[1].text(44,incumbent+.17,f'All five: {incumbent:.3f} h',ha='center',va='bottom',fontsize=7.5)
    handles=[Line2D([],[],color=c,marker=m,ms=4,lw=1.0,label=f'Seed {s}') for s,c,m in zip(SEEDS,COLORS,MARKERS)]
    handles.append(Line2D([],[],color='black',ls='--',lw=1.0,label='Impact-first incumbent'))
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.965),ncol=6,
        frameon=False,fontsize=7.5,handlelength=1.5,handletextpad=.45,columnspacing=1.05)
    fig.savefig(before,format='pdf',facecolor='white')
    fig.savefig(before.with_suffix('.png'),dpi=600,facecolor='white');plt.close(fig)
    with fitz.open(before) as d:
        p=d[0];spans=[s for b in p.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
        assert min(s['size'] for s in spans)>=7 and all(p.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
        assert all('Arial' in f[3] for f in p.get_fonts(full=True))
        p.get_pixmap(matrix=fitz.Matrix(2,2)).save(Path('C:/ABAQUS/temp/AppData/Local/Temp/la_s05_after_20261007.png'))
    record={'source_commit':'3e1b0a318eb54b3c384c02d66a71a71dcdfdb1b6','input_tables':inputs,
        'incumbent_loss_h':incumbent,'seeds':SEEDS,'generations_per_seed':101,
        'coincident_best_so_far_traces':all(np.allclose(v,incumbent,atol=1e-12,rtol=0) for h,v in histories),
        'final_loss_h':[-float(v) for v in final.fitness],
        'planning_horizon_h':horizon['H_plan_hr'],
        'pdf_sha256':sha(before),'png_sha256':sha(before.with_suffix('.png')),
        'minimum_font_pt':min(s['size'] for s in spans),'size_mm':[185,90],
        'ga_execution_invoked':False}
    path=ROOT/'docs/reproducibility/S05_GA_INCUMBENT_DISPLAY_20261007.json'
    path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');return record

def integrate(record):
    generator=Path(__file__).relative_to(ROOT).as_posix()
    def update_csv(path,fn):
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
        for row in rows:fn(row)
        with path.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    def index(row):
        if row['figure_number']!='FigS05':return
        source=ROOT/row['source_path'];shutil.copy2(source,ROOT/'results/figures'/row['file'])
        row.update(generator=generator,sha256_or_lfs_oid='sha256:'+sha(source),
            scientific_content='Five-seed best-so-far planning loss and final results relative to Impact-first',
            main_message='Each seed retained the initial Impact-first incumbent; no search improved it within the tested budget.',
            notes='Best-so-far includes the initial incumbent; all five traces coincide. Symbols sample actual generations without perturbing values.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    def manifest(row):
        if not row['final_name'].startswith('Supplement/FigS05.'):return
        p=REVIEW/row['final_name'];original=HISTORY/row['final_name']
        row.update(source_file=p.relative_to(ROOT).as_posix(),current_source_file=p.relative_to(ROOT).as_posix(),
            parent_source_file=original.relative_to(ROOT).as_posix(),parent_source_commit=record['source_commit'],parent_sha256=sha(original),
            source_commit='S05_GA_DISPLAY_UPDATE_20261007',sha256=sha(p),size_mm='185.000 x 90.000',min_font_pt='7.500',status='AUTHOR_REQUESTED_CURRENT_DISPLAY')
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    caption='Genetic algorithm (GA) search used 64 independent 2pc50 planning realizations and five seeds (42–46), over 100 generations. (A) Best-so-far population-weighted cumulative service loss on the planning realizations, by generation. Each best-so-far archive includes the initial deterministic incumbent. The five traces coincide with the Impact-first reference to numerical precision from generation 0 onward; the separate seed symbols identify original trace values at the indicated generations, without offsetting their values. (B) Final best planning loss for each seed, with the same Impact-first reference (black dashed line; 33.578 h). Panels share the same hour scale. No interval or uncertainty distribution is encoded by the seed points. Planning losses use the common pre-search horizon of 2,855.254 h, determined from planning inputs; it is distinct from the 480 h evaluation window. Impact-first had the lowest planning loss among the seven deterministic incumbents. No seed found a sequence improving on that incumbent within the tested search budget; this does not establish global optimality. Evaluation realizations were not used for strategy selection. The retained sequence equals Impact-first and is not an additional scheduled policy.'
    path=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';content=path.read_text(encoding='utf-8')
    pattern=r'(?ms)(^## Supplementary Figure S5\.[^\n]*\n\n).*?(?=^## |\Z)'
    content,count=re.subn(pattern,lambda m:m.group(1)+caption+'\n\n',content);assert count==1
    path.write_text(content,encoding='utf-8')
    keys=[f'Main/Fig{i:02}.pdf' for i in range(1,8)]+[f'Supplement/FigS{i:02}.pdf' for i in [1]+list(range(3,14))]
    book=fitz.open()
    for key in keys:
        if key.startswith('Supplement/'):
            with fitz.open(REVIEW/key) as d:book.insert_pdf(d)
    book.save(REVIEW/'ALL_SUPPLEMENT_FIGURES.pdf',garbage=4,deflate=True);book.close()
    parts=list(re.finditer(r'(?m)^## (.+)\n\n',content));lookup={}
    for i,m in enumerate(parts):
        title=m.group(1);body=content[m.end():parts[i+1].start() if i+1<len(parts) else len(content)].strip()
        if title.startswith('Figure '):key=f'Main/Fig{int(title.split(".")[0].replace("Figure ","")):02}.pdf'
        elif title.startswith('Supplementary Figure S'):key=f'Supplement/FigS{int(title.split(".")[0].replace("Supplementary Figure S","")):02}.pdf'
        else:continue
        lookup[key]=(title,body)
    book=fitz.open()
    for key in keys:
        with fitz.open(REVIEW/key) as d:book.insert_pdf(d)
        title,body=lookup[key];p=book.new_page(width=185*MM,height=350*MM)
        p.insert_font(fontname='PacketArial',fontfile=ARIAL);p.insert_font(fontname='PacketArialBold',fontfile=BOLD)
        assert p.insert_textbox(fitz.Rect(14*MM,16*MM,171*MM,28*MM),title,fontname='PacketArialBold',fontsize=9.5)>=0
        assert p.insert_textbox(fitz.Rect(14*MM,31*MM,171*MM,333*MM),body,fontname='PacketArial',fontsize=9.2,lineheight=1.22)>=0
    assert len(book)==38;book.save(REVIEW/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()
    authority=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';data=json.loads(authority.read_text(encoding='utf-8'))
    data['current_code_files']=[r for r in data['current_code_files'] if r['path']!=generator]+[{'path':generator,'sha256':sha(__file__),'tracked_in_current_git':True}]
    authority.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':integrate(render())
