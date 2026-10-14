"""Author-requested wording, cool population palette and continuous supplement numbering.

No models or simulations run. Figure 7 is an immutable source pending new instructions.
"""
from pathlib import Path
import io
import json
import re
import sys

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

import consolidate_current_figure_suite as u
from simplify_s05_figure_text_20261012 import plain_font
from integrate_final_s05_and_suite_review_20261012 import streams, RGB

ROOT=u.ROOT
DEST=ROOT/'results/figure_review'
QA=ROOT/'docs/reproducibility/figure_suite_author_clarity_numbering_20261013'
BASE='3c7899f0f328d37b99d2b022f1650c5288a4a664'
GEN='src/la_grid/plotting/apply_author_clarity_numbering_20261013.py'
MM=72/25.4
OLD_NUMBERS=[1,*range(3,12)]
NUMBER_MAP={old:new for new,old in enumerate(OLD_NUMBERS,1)}
OLD_ACTIVE=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in OLD_NUMBERS]
ACTIVE=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in range(1,11)]
CHANGED_OLD={'Main/Fig01','Supplement/FigS05','Supplement/FigS06','Supplement/FigS10'}
SOURCES={}


def source(rel):
    data=u.payload(BASE,rel)
    SOURCES[rel]={'commit':BASE,'sha256':u.digest(data),'bytes':len(data)}
    return data


def current_stem(old):
    match=re.fullmatch(r'Supplement/FigS(\d+)',old)
    return f'Supplement/FigS{NUMBER_MAP[int(match[1])]:02d}' if match else old


def refs(text):
    return re.sub(r'\bS(\d{1,2})\b',lambda m:'S'+str(NUMBER_MAP[int(m[1])])
                  if int(m[1]) in NUMBER_MAP else m[0],text)


def protection():
    if '--portable' in sys.argv and not Path(u.lp(u.ORIGINAL)).is_dir():
        before=QA/'PRESERVATION_BEFORE.json'
        if not before.exists():raise FileNotFoundError('Committed preservation record is required')
        u.dump(QA/'PORTABLE_REPLAY_NOTICE.json',{'local_original_worktree_reverified':False,
            'reason':'Frozen source checkout is not present; historical preservation record retained'})
        return json.load(open(u.lp(before)))
    prefix='docs/data_research/stage7_fig7d_policy_robustness_and_final_integration_gate_20261013/'
    record=json.loads(u.payload('05a78645b17bf8de04326e54181f9db432d7186c',prefix+'STARTING_STATE_AND_PROTECTION.json'))
    state=u.protected_snapshot(record)
    assert state['protected_files']==record['protected_files']
    return state


def prepare():
    u.dump(QA/'PRESERVATION_BEFORE.json',protection())
    for rel in u.git('ls-files','-z').decode().split('\0'):
        path=ROOT/rel
        if rel and Path(u.lp(path)).is_file() and open(u.lp(path),'rb').read(44).startswith(b'version https://git-lfs'):
            u.write(path,source(rel))
    for rel in ['.gitattributes','.gitignore']:
        if not (ROOT/rel).exists():u.write(ROOT/rel,u.git('show',BASE+':'+rel))
    manifest=u.csv_rows(source('results/figure_review/FIGURE_MANIFEST.csv'))
    backup={}
    for r in manifest:
        assert u.sha(ROOT/r['current_source_file'])==r['sha256']
        # A real untouched companion worktree and the immutable commit are backups before renaming.
        other=ROOT.parent/'_fa13'/r['current_source_file']
        assert u.sha(other)==r['sha256']
        backup[r['current_source_file']]=r['sha256']
    u.dump(QA/'BASELINE_AND_BACKUP.json',{'HEAD':BASE,'source_branch':'review/official-figure7-candidateA-approved-20261013',
        'implementation_branch':u.git('branch','--show-current').decode().strip(),
        'original_source_index_SHA256':u.sha(Path(u.git('rev-parse','--path-format=absolute','--git-path','index',root=ROOT.parent/'_fa13').decode().strip())),
        'real_unchanged_backup_worktree':str(ROOT.parent/'_fa13'),'artwork_SHA256':backup,
        'current_Fig07_locked':True})


def native(stem):
    return fitz.open(stream=source('results/figure_review/'+stem+'.pdf'),filetype='pdf')


def font(page,doc):
    regular=plain_font(page,doc,'AuthorArial','C:/Windows/Fonts/arial.ttf')
    bold=plain_font(page,doc,'AuthorBold','C:/Windows/Fonts/arialbd.ttf')
    return regular,bold


def text(page,fonts,x,y,value,size=7.5,bold=False,align='left',color=(.125,.145,.169),rotate=0):
    face=fonts[int(bold)]
    if align=='center':x-=face.text_length(value,fontsize=size)/2
    elif align=='right':x-=face.text_length(value,fontsize=size)
    page.insert_text((x,y),value,fontsize=size,fontname='AuthorBold' if bold else 'AuthorArial',color=color,rotate=rotate)


def spans(page):
    return [s for b in page.get_text('dict',flags=0)['blocks'] for l in b.get('lines',[]) for s in l['spans']]


def remove_text(page,selected):
    for s in selected:page.add_redact_annot(fitz.Rect(s['bbox'])+(-.05,-.05,.05,.05),fill=False)
    page.apply_redactions(images=0,graphics=0)


def edit_fig1():
    d=native('Main/Fig01');p=d[0]
    selected=[s for s in spans(p) if s['size']>=6.5 and
              ((s['bbox'][0]>94*MM and s['bbox'][1]>170*MM) or s['text']=='T80')]
    remove_text(p,selected);fonts=font(p,d)
    text(p,fonts,11*MM,182*MM,'80% service',7,color=(.72,.36,.29))
    for x,label in [(110,'Recovery outcomes'),(139,'Vulnerability groups'),(168,'Spatial patterns')]:
        text(p,fonts,x*MM,174*MM,label,7.5,True,'center')
    for i in range(4):text(p,fonts,(130+6*i)*MM,195.4*MM,'Q'+str(i+1),7.5,align='center')
    rows=[(110,200,'Service loss'),(110,205.5,'Time to 80% service'),(110,209,'(T80)'),
          (139,200,'Service loss by quartile'),(139,206,'|Q4-Q1| loss gap'),(139,212,'Gini'),
          (168,200,'Service-loss gap'),(168,206,'Community typology'),
          (168,211,'High vulnerability +'),(168,214.5,'slow-recovery hotspots')]
    for x,y,label in rows:text(p,fonts,x*MM,y*MM,label,7.5,align='center')
    u.dump(QA/'FIG01_WORDING_QA.json',{'stage5_body_font_pt':7.5,'T80_definition':'Time to 80% modeled service',
        'quartile_sequence':'Service loss by Q1, Q2, Q3 and Q4, not subtraction',
        'gap':'Absolute Q4-Q1 service-loss difference within each realization',
        'schematic_word_removed_from_artwork':True,'hotspot_direction':'High vulnerability AND slow recovery',
        'Fig07_or_hotspot_definition_changed':False,'text_changes':[s['text'] for s in selected]})
    return d


def edit_ga():
    d=native('Supplement/FigS05');p=d[0];old=spans(p)
    replace={'B. Initial and final planning loss':'B. Initial and final minimum loss',
        '20 runs; 64 planning realizations':'20 GA runs; 64 optimization realizations',
        'Initial and final loss for 20 runs':'One initial and one final result per GA run',
        'Distinct objective evaluations (thousands)':'Repair sequences evaluated (thousands)',
        'Best planning service loss (h)':'Minimum service loss (h)',
        'Planning service loss (h)':'Service loss (h)',
        'Median best-so-far loss':'Median minimum loss',
        'Final best':'Final minimum','100,000 evaluations':'20 GA runs',
        'C. Independent physical validation':'C. Independent validation',
        '2,000 paired validation realizations':'2,000 validation realizations',
        'GA minus Impact-first service loss (h)':'Service-loss gap (h)',
        'Self loss':'Substation-damage loss','Threshold loss':'Threshold-related loss',
        'Source-path loss':'Source-path loss','Net difference':'Total gap',
        'Change from Impact-first (h)':'Service-loss gap (h)'}
    ci_text=[s for s in old if 65<s['bbox'][0]<200 and 328<s['bbox'][1]<406 and
             (s['text'].startswith(('Paired mean','Simultaneous','[-0.')) or s['text'] in ['\u22120.56','\u22120.53','\u22120.50'])]
    selected=[s for s in old if s['text'] in replace]+ci_text
    remove_text(p,selected)
    # The CI inset sits above the ECDF tail and away from its mean/zero guide lines.
    # Cover only the obsolete inset; the actual frozen ECDF and all bars stay intact.
    p.draw_rect(fitz.Rect(65,329,178,405),color=None,fill=(1,1,1))
    fonts=font(p,d)
    for s in selected:
        if s['text'] not in replace:continue
        label=replace[s['text']];x,y=s['origin'];size=s['size'];rot=0;align='left'
        if s['text'] in ['Best planning service loss (h)','Planning service loss (h)']:
            y=(s['bbox'][1]+s['bbox'][3])/2+fonts[0].text_length(label,fontsize=size)/2
            rot=90
        elif s['text'] in ['Self loss','Threshold loss','Source-path loss','Net difference']:
            x=s['bbox'][2];align='right'
        elif s['text'] in ['Distinct objective evaluations (thousands)','GA minus Impact-first service loss (h)',
                           'Change from Impact-first (h)','Final best','100,000 evaluations']:
            x=(s['bbox'][0]+s['bbox'][2])/2;align='center'
        text(p,fonts,x,y,label,size,s['text'].startswith(('B.','C.')),align,color=(0,0,0),rotate=rot)
    text(p,fonts,78,344,'Mean: -0.533 h',8,color=(.12,.16,.18))
    text(p,fonts,78,356,'Gap = GA - Impact-first',7.5,color=(.12,.16,.18))
    u.dump(QA/'GA_LABEL_AND_ESTIMAND_QA.json',{'baseline_pdf_SHA256':u.digest(source('results/figure_review/Supplement/FigS05.pdf')),
        'independent_refers_to':'Validation realizations independent of optimization realizations',
        'evaluation_axis':'Unique repair-sequence objective scores per optimizer run, not independent physical samples',
        'GA_runs':20,'initial_random_orders_per_run':100,'evaluation_budget_per_run':100000,
        'optimization_realizations':64,'validation_realizations':2000,
        'mean_gap_h_frozen':-.532675,'CI_inset_removed_from_display':True,
        'physical_samples_sequences_curves_and_component_values_unchanged':True,
        'Cell_or_Self_loss_replaced_by':'Substation-damage loss'})
    return d


def edit_gate_definitions():
    from source_only_frozen_control_20261013 import calculate, POLICIES
    values=calculate()
    old=native('Supplement/FigS06')
    result=fitz.open();page=result.new_page(width=185*MM,height=220*MM)
    page.show_pdf_page(fitz.Rect(0,0,185*MM,66*MM),old,0,
                       clip=fitz.Rect(0,0,185*MM,66*MM))
    # Retain the two threshold plots without scaling; move them below the new source control.
    page.show_pdf_page(fitz.Rect(0,140*MM,185*MM,215*MM),old,0,
                       clip=fitz.Rect(0,70*MM,185*MM,145*MM))
    plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,
                         'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42})
    fig=plt.figure(figsize=(185/25.4,70/25.4))
    ax=fig.add_axes([.21,.25,.76,.53])
    colors=['#df8b21','#555555','#549b48'];markers=['s','o','^']
    for y,(policy,color,marker) in enumerate(zip(POLICIES,colors,markers)):
        row=values.loc[values.policy.eq(policy)&values.case.eq('G4_SOURCE_OFF_050')].iloc[0]
        ax.plot([row.p05_gap_h,row.p95_gap_h],[y,y],color=color,lw=1.2)
        ax.plot(row.mean_gap_h,y,marker=marker,color=color,ms=4)
        ax.text(row.mean_gap_h,y-.16,f'{row.mean_gap_h:+.3f}',ha='center',va='bottom',fontsize=8)
    ax.set_yticks(range(3),['Impact-first','Hospital-first','Degree-first'])
    ax.set_ylim(2.45,-.45);ax.set_xlim(-7.5,.2);ax.set_xticks([-7,-6,-5,-4,-3,-2,-1,0])
    ax.set_xlabel('Service-loss gap (h)')
    ax.axvline(0,color='.45',lw=.7)
    ax.grid(axis='x',color='.9',lw=.5);ax.set_axisbelow(True)
    for side in ['top','right']:ax.spines[side].set_visible(False)
    for side in ['left','bottom']:ax.spines[side].set_color('.75')
    ax.tick_params(length=0)
    fig.text(.035,.94,'B. Source connectivity disabled; functionality threshold fixed at 0.50',
             fontsize=8,fontweight='bold',va='top')
    fig.text(.21,.075,'Mean and 5th-95th realization percentiles; gap = source-off - reference',fontsize=7.5)
    buffer=io.BytesIO();fig.savefig(buffer,format='pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
    with fitz.open(stream=buffer.getvalue(),filetype='pdf') as source_plot:
        page.show_pdf_page(fitz.Rect(0,66*MM,185*MM,136*MM),source_plot,0)
    # Keep the nested original clipping intact. Redacting a reused clipped Form
    # would expose hidden historical labels and ticks outside the source crop.
    page.draw_rect(fitz.Rect(3*MM,140*MM,182*MM,146.8*MM),color=None,fill=(1,1,1))
    for center,label in [(61.4,'C. Functionality threshold: 0.05'),
                         (147.9,'D. Functionality threshold: 0.75')]:
        width=fitz.get_text_length(label,fontname='hebo',fontsize=9)
        page.insert_text((center*MM-width/2,143.26*MM),label,fontname='hebo',fontsize=9)
    page.insert_text((6*MM,138*MM),
        'C and D retain source connectivity; only the functionality threshold changes.',
        fontname='helv',fontsize=7.5)
    old.close()
    return result


def edit_population_palette():
    d=native('Supplement/FigS10')
    old=plt.get_cmap('YlOrBr')(.07+.73*np.linspace(0,1,256)**3)[:,:3]
    cool=plt.get_cmap('Blues')(np.linspace(.08,.72,256))[:,:3]
    edits=0;proof=[]
    for x in streams(d):
        raw=d.xref_stream(x)
        def change(m):
            nonlocal edits
            if m[4]!=b'rg':return m[0]
            col=np.array([float(m[k]) for k in [1,2,3]])
            diff=np.max(abs(old-col),axis=1);i=int(diff.argmin())
            if diff[i]<2e-6:
                edits+=1;return ('%.9f %.9f %.9f rg'%tuple(cool[i])).encode()
            return m[0]
        revised=RGB.sub(change,raw)
        if revised!=raw:
            assert RGB.sub(b'PAINT',raw)==RGB.sub(b'PAINT',revised)
            proof.append(u.digest(RGB.sub(b'PAINT',raw)))
            d.update_stream(x,revised)
    images=[]
    for x in range(1,d.xref_length()):
        if d.xref_get_key(x,'Subtype')[1]!='/Image':continue
        cs=d.xref_get_key(x,'ColorSpace')[1];m=re.search(r'<([0-9a-fA-F]+)>',cs)
        if not m:continue
        rgb=np.frombuffer(bytes.fromhex(m[1]),dtype=np.uint8).reshape(-1,3)/255
        mapped=[]
        for col in rgb:
            distance=np.max(abs(old-col),axis=1);i=int(distance.argmin());assert distance[i]<.01
            mapped.append(np.rint(cool[i]*255).astype(np.uint8))
        indices=u.digest(d.xref_stream(x))
        d.xref_set_key(x,'ColorSpace',cs[:m.start(1)]+np.array(mapped,dtype=np.uint8).tobytes().hex()+cs[m.end(1):])
        assert u.digest(d.xref_stream(x))==indices
        images.append(indices)
    assert edits>2000 and len(images)==1
    u.dump(QA/'POPULATION_PALETTE_QA.json',{'metric':'Tract population, not Impact-first score',
        'palette':'Blues, truncated 0.08-0.72','paint_operators_changed':edits,
        'all_noncolor_stream_bytes_SHA256':proof,'colorbar_scalar_index_SHA256':images,
        'population_values_log_normalization_ticks_geometry_rank_labels_unchanged':True,
        'dark_priority_markers_unchanged':True})
    return d


def export(doc,stem):
    path=DEST/(stem+'.pdf')
    u.write(path,doc.tobytes(garbage=4,deflate=True,no_new_id=True));doc.close()
    from build_current_suite_k3 import export_png
    export_png(stem)


def captions():
    caps=u.captions(source('results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    revised={}
    for h,b in caps.items():
        if h.startswith('Figure 1.'):
            b=b.replace('Community typology and spatial service-deficit patterns describe modeled community outcomes rather than repair priorities.',
                'Community typology, service-loss gaps and high-vulnerability/slow-recovery hotspot screening are distinct spatial outcomes, not repair priorities.')
            b += (' T80 is the time to 80% modeled service availability. Q1-Q4 are the frozen SOVI quartiles. '
                  '|Q4-Q1| denotes the absolute quartile difference in service loss within each realization.')
        if h.startswith('Supplementary Figure S5.'):
            b=('(A) Minimum service loss reached as repair sequences are evaluated in each of 20 frozen GA runs. Each run starts from 100 random repair orders and has a budget of 100,000 unique repair-sequence scores. '
               'All candidate orders are scored on the same 64 optimization realizations; the horizontal axis counts orders, not independent physical samples. Light curves are the 20 runs; the dark curve is their median minimum loss. '
               '(B) One initial minimum and one final minimum from each of those same 20 runs. Final refers to the endpoint of each run, not to one pooled observation from 20 runs. The selected run is marked by a diamond. '
               '(C) The selected frozen GA order and Impact-first are evaluated on the same 2,000 validation realizations, independent of the optimization set. The curve is the empirical distribution of the service-loss gap, defined as GA minus Impact-first. Negative means less loss under GA. The mean gap is -0.532675 h; 1,741 realizations have lower loss and 259 have higher loss. Only the mean is annotated; no confidence interval is displayed. '
               '(D) The same mean gap is decomposed into substation-damage loss (+0.277475 h), functionality-threshold loss (+0.010638 h) and source-path loss (-0.820788 h), summing to -0.532675 h within rounding. These are modeled components, not losses assigned to an unspecified cell or customer. '
               'Service loss is the 0-480 h integral of one minus modeled service availability under frozen 2pc50/C57_D1 inputs.')
        if h.startswith('Supplementary Figure S6.'):
            h='Supplementary Figure S6. Dependency mapping, source connectivity and functionality thresholds'
            b=('(A) Service-loss differences under candidate-weight cutoffs of zero, 1% and the 3% production cutoff, with the source gate and functionality threshold unchanged. '
               '(B) Source connectivity is disabled while the functionality threshold remains 0.50. The independent control uses the same frozen station states, repair orders, tract weights and 1,000 physical realizations per strategy. '
               'From the exact frozen loss decomposition, source-off loss equals reference loss minus source-path loss. The mean gaps are -4.167720 h (Impact-first), -4.065130 h (Hospital-first) and -2.418438 h (Degree-first). '
               '(C, D) Only the functionality threshold changes, to 0.05 or 0.75; source connectivity remains required. Points show means and lines show the 5th-95th realization percentiles, not confidence intervals. '
               'Each gap is the indicated control minus the 0.50/source-connected reference. Source connectivity means a path to a retained Core source; functionality eligibility means f >= threshold. '
               'All B-D comparisons use 2pc50, C57_D1, M1_UTILITY_003 and the 0-480 h population-weighted modeled service-loss integral over all 2,315 study tracts. '
               'The source-only control is a diagnostic relaxation, not evidence of physical electricity delivery.')
        if h.startswith('Supplementary Figure S10.'):
            b=b.replace('warm sequential','muted blue sequential').replace('warm population scale','blue population scale')
        revised[refs(h)]=refs(b)
    return revised


def main():
    checkpoint=QA/'BUILD_CHECKPOINT.json'
    routing='src/la_grid/plotting/build_current_suite_k3.py'
    control='src/la_grid/plotting/source_only_frozen_control_20261013.py'
    if checkpoint.exists() and '--rebuild' not in sys.argv:
        q=json.load(open(u.lp(checkpoint)))
        if (q['generator_SHA256']==u.sha(ROOT/GEN) and q['routing_SHA256']==u.sha(ROOT/routing)
            and q.get('source_control_generator_SHA256')==u.sha(ROOT/control)
            and all(Path(u.lp(ROOT/p)).is_file() and u.sha(ROOT/p)==h for p,h in q['output_hashes'].items())):
            print('Author clarity/continuous-numbering suite: byte-identical replay.');return
    if not (QA/'PRESERVATION_BEFORE.json').exists():
        raise RuntimeError('Run --prepare first to preserve original science and source artwork')
    manifest=u.csv_rows(source('results/figure_review/FIGURE_MANIFEST.csv'))
    index=u.csv_rows(source('results/figures/FIGURE_INDEX.csv'))
    # Read every immutable source before overwriting any numbered destination.
    artwork={r['final_name']:source(r['current_source_file']) for r in manifest}
    for r in manifest:assert u.digest(artwork[r['final_name']])==r['sha256']
    for r in manifest:
        old=r['final_name'].rsplit('.',1)[0];ext=r['final_name'].rsplit('.',1)[1]
        u.write(DEST/(current_stem(old)+'.'+ext),artwork[r['final_name']])
    for old in OLD_ACTIVE:
        u.write(DEST/'Page_Previews'/(Path(current_stem(old)).name+'.png'),
                source('results/figure_review/Page_Previews/'+Path(old).name+'.png'))
    for old,func in [('Main/Fig01',edit_fig1),('Supplement/FigS05',edit_ga),
                     ('Supplement/FigS06',edit_gate_definitions),('Supplement/FigS10',edit_population_palette)]:
        export(func(),current_stem(old))
    updated=[];rows=[];changes=[]
    for r in manifest:
        row=r.copy();old,ext=row['final_name'].rsplit('.',1);new=current_stem(old)
        rel='results/figure_review/'+new+'.'+ext
        mirror=row['mirror_file']
        if old.startswith('Supplement/'):
            mirror=mirror.replace(Path(old).name,Path(new).name)
        row.update(final_name=new+'.'+ext,current_source_file=rel,mirror_file=mirror,
                   parent_source_commit=BASE,parent_source_file=r['current_source_file'],parent_sha256=r['sha256'])
        actual=u.sha(ROOT/rel);changed=old in CHANGED_OLD
        if not changed:assert actual==r['sha256']
        row['sha256']=actual;row['change_in_this_update']='UPDATED' if changed else 'RETAINED'
        row['presentation_generator']=GEN;row['presentation_generator_sha256']=u.sha(ROOT/GEN)
        row['additional_source_file']=''
        row['additional_source_sha256']=''
        if old=='Supplement/FigS06':
            row['additional_source_file']=str((QA/'SOURCE_ONLY_REALIZATION_VALUES.csv').relative_to(ROOT)).replace('\\','/')
            row['additional_source_sha256']=u.sha(QA/'SOURCE_ONLY_REALIZATION_VALUES.csv')
        with fitz.open(u.lp(DEST/(new+'.pdf'))) as doc:
            row['size_mm']=' x '.join(f'{v/MM:.3f}' for v in [doc[0].rect.width,doc[0].rect.height])
        u.write(ROOT/mirror,open(u.lp(ROOT/rel),'rb').read());rows.append(row)
        ix=next(x.copy() for x in index if x['source_path']==r['current_source_file'])
        ix.update(source_path=rel,file=Path(mirror).name,figure_number=Path(new).name,
                  sha256_or_lfs_oid=actual,generator=GEN,notes='Author wording/palette corrections; continuous supplement numbering; science unchanged.')
        if old=='Main/Fig01':ix['main_message']='Five-stage workflow; T80 defined; absolute Q4-Q1 gap; high-vulnerability/slow-recovery hotspot direction.'
        if old=='Supplement/FigS05':ix['main_message']='20 GA runs, repair sequences evaluated; independent validation; mean loss gap and named components.'
        if old=='Supplement/FigS06':
            ix.update(scientific_question='What are the separate effects of mapping cutoff, source connectivity and functionality threshold?',
                scientific_content='Independent source-only control at fixed 0.50 threshold; original 0.05/0.75 threshold controls retain source connectivity.',
                main_message='Separate mapping, source-only and threshold-only diagnostic comparisons on frozen results.',
                notes='Source-only values are exact post-processing; source authority and all sample hashes are recorded in the current QA package.')
        updated.append(ix)
        changes.append({'old_figure':old,'current_figure':new,'format':ext,'baseline_SHA256':r['sha256'],
            'current_SHA256':actual,'content_change':changed,'figure7_locked':old=='Main/Fig07'})
    # Remove only now-unassigned presentation paths after backup and exact immutable-source verification.
    allowed={r['current_source_file'] for r in rows}|{r['mirror_file'] for r in rows}
    for r in manifest:
        for rel in [r['current_source_file'],r['mirror_file']]:
            if rel not in allowed:
                path=ROOT/rel
                assert path.is_relative_to(ROOT) and rel.startswith(('results/figure_review/','results/figures/'))
                if Path(u.lp(path)).exists():Path(u.lp(path)).unlink()
    stale=DEST/'Page_Previews/FigS11.png'
    if stale.exists():stale.unlink()
    u.write_csv(DEST/'FIGURE_MANIFEST.csv',rows)
    u.write_csv(QA/'NUMBERING_AND_ARTWORK_CHANGES.csv',changes)
    caps=captions()
    u.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+'\n\n'.join('## '+h+'\n\n'+b for h,b in caps.items())+'\n')
    from build_current_suite_k3 import gallery
    gallery(updated)
    palette=json.loads(source('results/figure_review/CURRENT_CLUSTER_PALETTE.json'))
    palette['applies_to']=[re.sub(r'FigS(\d{2})',lambda m:f'FigS{NUMBER_MAP[int(m[1])]:02d}',s)
                           for s in palette['applies_to']]
    u.dump(DEST/'CURRENT_CLUSTER_PALETTE.json',palette)
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    from reportlab import rl_config
    rl_config.invariant=1
    books=[fitz.open(),fitz.open(),fitz.open()]
    for stem,(heading,body) in zip(ACTIVE,caps.items()):
        with fitz.open(u.lp(DEST/(stem+'.pdf'))) as doc:
            books[0 if stem.startswith('Main/') else 1].insert_pdf(doc);books[2].insert_pdf(doc)
        with u.caption_pdf(heading,body) as cap:books[2].insert_pdf(cap)
    with fitz.open(stream=source('results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf') as prior:
        books[2].insert_pdf(prior,from_page=34,to_page=37)
    for name,book,count in zip(['ALL_MAIN_FIGURES','ALL_SUPPLEMENT_FIGURES','ALL_FIGURES_WITH_CAPTIONS'],books,[7,10,38]):
        assert len(book)==count
        u.write(DEST/(name+'.pdf'),book.tobytes(garbage=4,deflate=True,no_new_id=True));book.close()
    readme=('# Current publication figures\n\nMain Fig01-Fig07; Supplement FigS01-FigS10: 17 numbered figures, 38 packet pages. '
        'Numbering is continuous: former S03-S11 shifted down one position because former S02 content was already merged into S01. '
        'Current S02 is former S03, not the retired artwork. See NUMBERING_AND_ARTWORK_CHANGES.csv.\n\n'
        'Figure 7 remains byte-identical to 3c7899f pending the next author instruction for its hotspot panel. '
        'Figure 1 states the intended high-vulnerability/slow-recovery hotspot concept without calculating a new score. '
        'Former S09 C/D and former S11 are retained, renumbered to S08 and S10; their necessity is reviewed separately, not assumed to validate the selected model.\n\n'
        'Canonical build: `python src/la_grid/plotting/build_current_suite_k3.py --portable`. '
        'Use `--rebuild` for immutable-source replay. No model, optimization, simulation or scientific source is altered.\n\n'
        'Current S05 separates the mapping cutoff, a newly calculated source-only control at fixed 0.50 functionality threshold, and the saved threshold-only comparisons. '
        'The control is exact post-processing of frozen station-loss integrals, not a new physical or scheduling simulation.\n')
    u.write(DEST/'README.md',readme);u.write(ROOT/'results/figures/README.md',readme+'\nMirrors match authoritative artwork bytes.\n')
    u.write(DEST/'UPDATE_LOG.md',source('results/figure_review/UPDATE_LOG.md').decode()+
        '\n\n## 2026-10-13 Author clarity and continuous numbering\n\n'
        'Former S03-S11 now S02-S10. Fig01 definitions/fonts, former S05 language/mean-only annotation, former S06 independent source-only control and separate threshold panels, '
        'and former S10 cool population palette updated. Fig07 and all scientific data unchanged. S09/S11 content questions remain review decisions.\n')
    assert u.sha(DEST/'Main/Fig07.pdf')==u.digest(source('results/figure_review/Main/Fig07.pdf'))
    after=protection();assert after==json.load(open(u.lp(QA/'PRESERVATION_BEFORE.json')))
    u.dump(QA/'PRESERVATION_AFTER.json',after);u.dump(QA/'SOURCE_HASHES.json',SOURCES)
    outputs=[r['current_source_file'] for r in rows]+[r['mirror_file'] for r in rows]
    outputs += ['results/figure_review/'+n for n in ['FIGURE_MANIFEST.csv','MANUSCRIPT_FACING_CAPTIONS.md','CURRENT_CLUSTER_PALETTE.json','ALL_MAIN_FIGURES.pdf',
        'ALL_SUPPLEMENT_FIGURES.pdf','ALL_FIGURES_WITH_CAPTIONS.pdf','README.md','UPDATE_LOG.md']]
    outputs += ['results/figures/'+n for n in ['FIGURE_INDEX.csv','FIGURE_REVIEW_GALLERY.html','README.md']]
    outputs += ['results/figure_review/Page_Previews/'+Path(s).name+'.png' for s in ACTIVE]
    u.dump(checkpoint,{'generator_SHA256':u.sha(ROOT/GEN),'routing_SHA256':u.sha(ROOT/routing),
        'source_control_generator_SHA256':u.sha(ROOT/control),
        'output_hashes':{p:u.sha(ROOT/p) for p in outputs}})
    print('Continuous S01-S10; Fig01 and former S05/S06/S10 corrected; Fig07 frozen; 950 scientific files preserved.')


if __name__=='__main__':
    prepare() if '--prepare' in sys.argv else main()
