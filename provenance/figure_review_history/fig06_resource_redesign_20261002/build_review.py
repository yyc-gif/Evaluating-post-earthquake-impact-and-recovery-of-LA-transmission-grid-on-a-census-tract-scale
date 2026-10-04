"""Presentation only: read accepted results; never execute a scientific stage.

Outputs are isolated review candidates. In particular nothing is promoted to
results/figures. Intervals in the preferred figure are copied from the saved
paired-effects tables, not recomputed or replaced with realization percentiles.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
LAYOUT = ROOT / 'results/figure_review/candidate_v2.1_layout'
EQ = ROOT / 'Formal_Experiment_20260923/Equity_Amendment'
FORMAL = ROOT / 'Formal_Experiment_20260923/Formal_Results'
MM = 72 / 25.4
plt.rcParams.update({'font.family':'Arial', 'font.size':7.5,
    'axes.titlesize':9.5, 'axes.labelsize':8.5, 'xtick.labelsize':7.5,
    'ytick.labelsize':7.5, 'legend.fontsize':7.5, 'axes.linewidth':.6,
    'grid.linewidth':.4, 'pdf.fonttype':42, 'ps.fonttype':42,
    'savefig.facecolor':'white', 'figure.facecolor':'white'})
METRICS = ['burden_Q4_hr', 'population_weighted_normalized_burden_hr',
           'absolute_Q4_minus_Q1_hr']
CREW = ['C29_D1','C57_D1','C86_D1','C114_D1']
DURATION = ['C57_D075','C57_D1','C57_D125','C57_D150']
REFERENCES = ['hospital-first','impact-first']
REF_STYLE = {'hospital-first':('#555555','o','Hospital-first'),
             'impact-first':('#ff7f00','s','Impact-first')}
CAPTIONS = {}
QA = []

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inspect_pdf(p):
    with fitz.open(p) as doc:
        page = doc[0]
        spans = [s for b in page.get_text('dict')['blocks'] if 'lines' in b
                 for l in b['lines'] for s in l['spans'] if s['text'].strip()]
        bad = [s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))]
        return {'file':p.name, 'width_mm':page.rect.width/MM,
                'height_mm':page.rect.height/MM,
                'min_text_pt':min(s['size'] for s in spans),
                'fonts':';'.join(sorted(set(s['font'] for s in spans))),
                'off_page_text':';'.join(bad), 'sha256':sha(p)}

def export(p):
    with fitz.open(p) as doc:
        for dpi,suffix in [(600,''),(150,'_preview')]:
            pix=doc[0].get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
            pix.set_dpi(dpi,dpi)
            pix.save(str(p.with_name(p.stem+suffix+'.png')))
    QA.append(inspect_pdf(p))

def save(fig,stem,caption):
    p=OUT/(stem+'.pdf')
    fig.savefig(p,dpi=600,metadata={'Title':stem.replace('_',' '),
                                   'Author':'Review candidate; not promoted'})
    plt.close(fig)
    CAPTIONS[stem]=caption
    export(p)
    return p

def read_inputs():
    effects=[]
    for name in ['VULNERABILITY_PAIRWISE_EFFECTS.csv','VULNERABILITY_RESOURCE_EFFECTS.csv']:
        d=pd.read_csv(EQ/name)
        d['source_authority']=(EQ/name).relative_to(ROOT).as_posix()
        effects.append(d)
    effects=pd.concat(effects,ignore_index=True)
    effects=effects[effects.hazard.eq('2pc50') & effects.metric.isin(METRICS)
                    & effects.reference_strategy.isin(REFERENCES)].copy()
    assert len(effects)==42
    assert not effects.duplicated(['resource_scenario','reference_strategy','metric']).any()
    assert effects.n_realizations.eq(1000).all()
    columns=['hazard','resource_scenario','realization_id','strategy_id','mapping','gate',
             *METRICS,'hospital_mean_normalized_burden_hr']
    raw=pd.concat([pd.read_parquet(FORMAL/'PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',columns=columns),
                   pd.read_parquet(EQ/'VULNERABILITY_PRIMARY_SUMMARY.parquet',columns=columns)],ignore_index=True)
    raw=raw[raw.hazard.eq('2pc50') & raw.mapping.eq('M1_UTILITY_003') & raw.gate.eq('G1_BASELINE_050')]
    raw=raw[~raw.strategy_id.eq('direct-community')].copy()
    checks=[]
    for row in effects.itertuples():
        d=raw[raw.resource_scenario.eq(row.resource_scenario)]
        a=d[d.strategy_id.eq('vulnerability-first')].set_index('realization_id')[row.metric]
        b=d[d.strategy_id.eq(row.reference_strategy)].set_index('realization_id')[row.metric]
        assert len(a)==len(b)==1000 and a.index.sort_values().equals(b.index.sort_values())
        difference=float((a-b).mean())
        error=abs(difference-row.paired_mean_difference)
        assert error<1e-9,(row,error)
        checks.append({'condition':row.resource_scenario,'reference':row.reference_strategy,
                       'metric':row.metric,'saved_mean_parity_error':error})
    pd.DataFrame(checks).to_csv(OUT/'SAVED_VALUE_PARITY.csv',index=False)
    effects.to_csv(OUT/'PLOTTED_FROZEN_EFFECT_ROWS.csv',index=False)
    return effects,raw

def preferred(effects):
    fig=plt.figure(figsize=(185/25.4,166/25.4))
    gs=fig.add_gridspec(2,3,left=.115,right=.985,top=.79,bottom=.12,
                       hspace=.67,wspace=.50)
    fig.text(.5,.985,'Resource dependence of restoration-policy contrasts under 2pc50',
             ha='center',va='top',fontsize=10,fontweight='bold')
    fig.text(.5,.946,'2pc50  |  Difference = Vulnerability-first minus reference',
             ha='center',va='top',fontsize=8)
    handles=[Line2D([0],[0],marker=m,color=c,lw=0,markersize=4,
               label='Reference: '+label) for c,m,label in REF_STYLE.values()]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.914),
               ncol=2,frameon=False,columnspacing=1.7,handletextpad=.4)
    titles=['Q4 cumulative\nservice loss','Population-weighted\ncumulative service loss',
            'Absolute Q4–Q1\nseparation']
    panels=[]
    for i,cases in enumerate([CREW,DURATION]):
        for j,metric in enumerate(METRICS):
            ax=fig.add_subplot(gs[i,j])
            ax.set_title(chr(65+i*3+j)+'. '+titles[j],loc='left',fontsize=9.5,pad=7,fontweight='bold')
            relevant=effects[effects.metric.eq(metric)]
            lo=min(0,float(relevant.bootstrap_ci_low.min()))
            hi=max(0,float(relevant.bootstrap_ci_high.max()))
            padding=(hi-lo)*.12
            ax.set_ylim(lo-padding,hi+padding)
            ax.axhline(0,color='#343434',linewidth=.7,ls='--',zorder=1)
            for k,ref in enumerate(REFERENCES):
                color,marker,label=REF_STYLE[ref]
                for x,case in enumerate(cases):
                    row=effects[(effects.resource_scenario.eq(case)) &
                                effects.reference_strategy.eq(ref) & effects.metric.eq(metric)].iloc[0]
                    y=row.paired_mean_difference
                    ax.errorbar(x+(-.065 if k==0 else .065),y,
                         yerr=[[y-row.bootstrap_ci_low],[row.bootstrap_ci_high-y]],
                         fmt=marker,color=color,ecolor=color,ms=4.0,elinewidth=.8,
                         capsize=2.1,markeredgecolor='white',markeredgewidth=.4,zorder=4)
                    panels.append({'panel':chr(65+i*3+j),'condition':case,'metric':metric,
                         'reference':ref,'mean':y,'ci_low':row.bootstrap_ci_low,
                         'ci_high':row.bootstrap_ci_high,'source_authority':row.source_authority})
            ax.set_xticks(range(4),['29','57','86','114'] if i==0 else ['0.75','1.00','1.25','1.50'])
            ax.set_xlim(-.45,3.45)
            ax.set_xlabel('Repair crews\n(duration multiplier = 1.00)' if i==0 else
                          'Repair-duration multiplier\n(57 crews)',fontsize=8)
            ax.set_ylabel('Policy difference (h)',fontsize=8)
            ax.grid(axis='y',alpha=.18)
            ax.tick_params(length=2.5,width=.6)
    fig.text(.5,.038,'Points: matched means; whiskers: saved 95% bootstrap confidence intervals.',
             ha='center',va='center',fontsize=7.5)
    pd.DataFrame(panels).to_csv(OUT/'FIG06_PANEL_SOURCE_INDEX.csv',index=False)
    caption=('Resource dependence of restoration-policy contrasts under 2pc50. A–C compare 29, 57, 86 and 114 crews '
      'with the adopted repair-duration multiplier 1.00; D–F compare multipliers 0.75, 1.00, 1.25 '
      'and 1.50 with 57 crews. Every point is Vulnerability-first minus its explicitly named '
      'Hospital-first (gray circle) or Impact-first (orange square) reference, using 1,000 matched '
      'physical realizations per condition. Whiskers are the existing 95% bootstrap confidence '
      'intervals for the mean paired difference, copied from accepted tables; they are not 5th–95th '
      'realization ranges. All losses integrate 0–480 h. Q4 is the highest social-vulnerability '
      'quartile. Negative Q4 change denotes lower group loss; positive population change denotes '
      'greater population-weighted loss; positive absolute Q4–Q1 change denotes greater per-realization '
      'absolute group separation, summarized over realizations. Each column shares its y scale '
      'across the two scenario families. These are discrete one-factor cases: no continuous response, '
      'interpolation, factorial interaction, or universal scarcity claim is implied. The common '
      '57-crew/multiplier-1.00 case appears in both rows. Q4 benefit, aggregate efficiency and '
      'between-group separation are separate outcomes, and their directions can disagree. '
      'Gini is a separate overall inequality measure, reported in Fig05 and the supplement. '
      'Policy contrasts were largest under the most crew-constrained tested case and generally '
      'diminished at higher crew availability, while longer tested repair durations amplified '
      'Q4 and Q4–Q1 separation contrasts. Together, these tested cases indicate greater policy '
      'leverage when restoration capacity is more constrained relative to workload. '
      'Crew count and duration are two separate one-factor-at-a-time scenario families, '
      'not a unified calibrated capacity variable.')
    return save(fig,'Fig06_Preferred_Resource_Policy_Contrasts',caption)


def separation_detail(effects):
    """Review-only near-zero detail; preserve the preferred figure's common scales."""
    fig, ax = plt.subplots(figsize=(185/25.4,90/25.4))
    fig.subplots_adjust(left=.16,right=.98,bottom=.23,top=.67)
    fig.text(.5,.98,'Review-only detail: higher-crew between-group separation',
             ha='center',va='top',fontsize=9.5,fontweight='bold')
    handles=[Line2D([0],[0],marker=m,color=c,lw=0,markersize=4,
               label='Reference: '+label) for c,m,label in REF_STYLE.values()]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.88),
               ncol=2,frameon=False,columnspacing=1.7,handletextpad=.4)
    detail=effects[effects.metric.eq(METRICS[2]) & effects.resource_scenario.isin(CREW[2:])]
    lo=min(0,float(detail.bootstrap_ci_low.min()))
    hi=max(0,float(detail.bootstrap_ci_high.max())); padding=(hi-lo)*.18
    ax.set_ylim(lo-padding,hi+padding)
    ax.axhline(0,color='#343434',linewidth=.7,ls='--',zorder=1)
    for k,ref in enumerate(REFERENCES):
        c,m,_=REF_STYLE[ref]
        for x,case in enumerate(CREW[2:]):
            row=detail[detail.resource_scenario.eq(case) & detail.reference_strategy.eq(ref)].iloc[0]
            y=row.paired_mean_difference
            ax.errorbar(x+(-.065 if k==0 else .065),y,
                        yerr=[[y-row.bootstrap_ci_low],[row.bootstrap_ci_high-y]],
                        fmt=m,color=c,ecolor=c,ms=4,elinewidth=.8,capsize=2.1,
                        markeredgecolor='white',markeredgewidth=.4,zorder=4)
    ax.set_xticks([0,1],['86','114']);ax.set_xlim(-.4,1.4)
    ax.set_xlabel('Repair crews (duration multiplier = 1.00)',fontsize=8)
    ax.set_ylabel('Absolute Q4–Q1 separation\nchange relative to reference (h)',fontsize=8)
    ax.grid(axis='y',alpha=.18);ax.tick_params(length=2.5,width=.6)
    fig.text(.5,.055,'Local detail only; the main Fig06 common scales remain unchanged.',
             ha='center',fontsize=7.5)
    caption=('Review-only zoom of the four 86-/114-crew points already shown in Fig06C, '
        'with duration multiplier 1.00. Each point is Vulnerability-first minus Hospital-first '
        '(gray circle) or Impact-first (orange square). The local hour scale reveals the '
        'near-zero between-group separation contrasts; it does not replace or break the '
        'common axes of the six-panel figure. Whiskers reproduce the same saved 95% bootstrap '
        'confidence intervals for the mean paired difference across 1,000 matched realizations. '
        'The Impact-first interval at 86 crews crosses zero; the other three intervals do not. '
        'These small contrasts must not be described as a strictly monotonic crew effect. '
        'All source rows are the corresponding panel-C entries in FIG06_PANEL_SOURCE_INDEX.csv.')
    return save(fig,'Fig06_Separation_Detail_Review',caption)

def exact_comparison_copies():
    records=[]
    for source,dest in [
       ('Fig06_Two_Level_Crew_Resource_Contrast','Fig06_Previous_Two_Level_Comparison'),
       ('Candidate_Supplement_Crew_Resource_Contrasts','Full_Crew_Absolute_Outcomes'),
       ('Candidate_Supplement_Repair_Duration_Contrasts','Full_Duration_Absolute_Outcomes')]:
        p=OUT/(dest+'.pdf');s=LAYOUT/(source+'.pdf')
        shutil.copyfile(s,p); assert sha(p)==sha(s)
        export(p)
        records.append({'review_file':p.name,'source_authority':s.relative_to(ROOT).as_posix(),
                        'sha256':sha(s),'exact_copy':True})
        CAPTIONS[dest]=('Exact copy of the existing review artwork, retained for comparison; no result '
            'or style is changed. '+ ('Only 29 and 57 crews and four policies are displayed.' if dest.startswith('Fig06') else
            'All eight scheduled policies and all four tested levels are displayed. Points are means '
            'and whiskers are 5th–95th realization ranges; these are not confidence intervals. '
            'All cumulative losses integrate 0–480 h. There is no untested-level interpolation.'))
    pd.DataFrame(records).to_csv(OUT/'EXACT_COPY_IDENTITIES.csv',index=False)

def fix_fig05():
    # Call only the already-established presentation function, with export
    # redirected to this review folder. Do not call either module's main().
    spec=importlib.util.spec_from_file_location('review_layout',LAYOUT/'build_layout_candidates.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def export_fixed(fig,stem):
        original_values=[]
        a=fig.axes[0]
        for cont in a.containers:
            original_values.extend(np.asarray(cont.lines[0].get_ydata(),dtype=float))
        module.layout_05(fig);module.common_style(fig)
        for collection,key in zip(fig.axes[1].collections,module.v.STRATEGY_ORDER):
            if key not in module.v.CORE_POLICIES and key!='unconstrained':
                collection.set_alpha(.72)
        # Dodge categorical marks only, retaining every y value and interval.
        for k,cont in enumerate(a.containers):
            shift=(-.12,-.04,.04,.12)[k]
            line,caps,collections=cont.lines
            line.set_xdata(np.asarray(line.get_xdata(),dtype=float)+shift)
            for cap in caps:cap.set_xdata(np.asarray(cap.get_xdata(),dtype=float)+shift)
            for collection in collections:
                segments=collection.get_segments()
                for segment in segments:segment[:,0]+=shift
                collection.set_segments(segments)
        after=[]
        for cont in a.containers:after.extend(np.asarray(cont.lines[0].get_ydata(),dtype=float))
        assert np.array_equal(original_values,after)
        a.set_xlim(.70,4.30)
        # Two distinct marker shapes reinforce core-policy colors in the plane;
        # the policy legend already supplies a line/marker key.
        c,g=fig.axes[5:7]
        g.set_yticklabels(['Impact-first','Hospital-first','Degree-first'])
        g.set_xlabel('Vulnerability-first\nminus reference\n(unitless)',fontsize=7.5)
        # Give the small Gini panel's reference labels adequate horizontal room.
        module.box(fig,g,158,121,21,24)
        g.set_yticklabels(['Impact','Hospital','Degree'])
        caption=pd.read_csv(LAYOUT/'FIGURE_V2_1_LAYOUT_INDEX.csv').set_index('figure_stem').loc[stem,'caption']
        return save(fig,'Fig05_Separated_Quartile_Intervals',str(caption)+
            ' The quartile markers and intervals are horizontally dodged for visibility; '
            'categorical quartile identity and all y values are unchanged. This is a layout review, '
            'not a change in statistics. C and D share the explicitly named reference-policy key.')
    module.v.save_figure=export_fixed
    module.v.build_fig05(module.base.read_eval(),module.base.map_domain())

def improve_policy_and_cluster_visibility():
    spec=importlib.util.spec_from_file_location('visibility_layout',LAYOUT/'build_layout_candidates.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def write(fig,stem):
        signature=module.data_signature(fig)
        if stem.startswith('Fig04'):
            module.layout_04(fig);module.common_style(fig)
            for line in fig.axes[0].lines:
                if line.get_alpha() is not None and line.get_alpha()<.6:
                    line.set_alpha(.68)
            for ax in fig.axes[1:]:
                for key,container in zip(module.v.STRATEGY_ORDER,ax.containers):
                    if key not in module.v.CORE_POLICIES and key!='unconstrained':
                        for artist in [container.lines[0],*container.lines[1],*container.lines[2]]:
                            if artist is not None:artist.set_alpha(.75)
            caption=pd.read_csv(LAYOUT/'FIGURE_V2_1_LAYOUT_INDEX.csv').set_index('figure_stem').loc[stem,'caption']
            caption=str(caption).replace('availability over 0–120 h','availability over 0–100 h')
            dest='Fig04_Readable_All_Policy_Comparison'
        else:
            module.layout_support(fig,stem);module.common_style(fig)
            scatter=fig.axes[0]
            for collection in scatter.collections:collection.set_alpha(.9)
            for leg in fig.legends:
                for handle in leg.legend_handles:handle.set_alpha(1)
            caption=pd.read_csv(LAYOUT/'FIGURE_V2_1_LAYOUT_INDEX.csv').set_index('figure_stem').loc[stem,'caption']
            dest='FigS09_Cluster_Visibility'
        assert module.data_signature(fig)==signature
        return save(fig,dest,str(caption)+' Display opacity is increased for legibility; '
                     'all data coordinates, values, cluster colors and interval definitions are unchanged.')
    module.base.save_figure=write;module.v.save_figure=write
    module.base.build_fig04(module.base.read_eval())
    module.v.build_figs09()

def correct_supplement_wording():
    # Native PDF text replacement only; retain vector paths and every plotted
    # numerical value. Redaction rectangles are restricted to label text.
    sources=[('FigS03_Crew_Bases_and_Directed_Travel','FigS03_Clear_Input_Labels',
              {'Retained station (n=92)':'Substations (n=92)'}),
             ('FigS08_Capacity_Sensitivity','FigS08_Clear_Planning_Labels',
              {'SCE planning loading for retained source-reachable facilities':
               'SCE planning loading at source-reachable facilities',
               '2pc50: additional population burden under the capacity bound':
               '2pc50: additional population-weighted cumulative service loss',
               'Capacity-bounded minus baseline burden (h; expanded scale)':
               'Capacity-bounded minus baseline cumulative loss (h; expanded scale)'})]
    rows=[]
    for source,dest,replacements in sources:
        p=ROOT/'results/figures'/(source+'.pdf')
        with fitz.open(p) as doc:
            page=doc[0];page.insert_font(fontname='ReviewArial',fontfile='C:/Windows/Fonts/arial.ttf')
            spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b
                   for l in b['lines'] for s in l['spans']]
            edits=[]
            for old,new in replacements.items():
                found=[s for s in spans if s['text']==old]
                assert len(found)==1,(source,old)
                s=found[0];rect=fitz.Rect(s['bbox']);page.add_redact_annot(rect,fill=(1,1,1))
                edits.append((s,new))
            page.apply_redactions(images=0,graphics=0)
            page.insert_font(fontname='ReviewArial',fontfile='C:/Windows/Fonts/arial.ttf')
            page.insert_font(fontname='ReviewArialBold',fontfile='C:/Windows/Fonts/arialbd.ttf')
            for s,new in edits:
                x,y=s['origin'];font_size=max(7.5,s['size'])
                width=fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf').text_length(new,fontsize=font_size)
                if x+width>page.rect.width-3:
                    x=max(3,(page.rect.width-width)/2)
                page.insert_text((x,y),new,fontname='ReviewArialBold' if 'Bold' in s['font'] else 'ReviewArial',fontsize=font_size)
            target=OUT/(dest+'.pdf');doc.save(target,garbage=4,deflate=True)
        export(target)
        rows.append({'review_file':target.name,'source_authority':p.relative_to(ROOT).as_posix(),
                     'changes':'Reader-facing labels only; original numerical content retained'})
        CAPTIONS[dest]=('Presentation-label correction of the existing publication figure. '
            'The map geometry, numerical results, discrete cases and plot arrangement remain unchanged. '
            'Crew/travel panels are inputs, not resource-response evidence; SCE loading is planning '
            'evidence, not post-earthquake load flow. No scientific result is regenerated.')
    pd.DataFrame(rows).to_csv(OUT/'SUPPLEMENT_LABEL_CHANGES.csv',index=False)

def compact_native_fig07():
    """Reflow existing paths/images; restore every text span at original size.

    No KDE fit, PCA, clustering, profile calculation or map generation occurs.
    Only plot-box vertical proportions change. Map row is exactly native size.
    Native text is replaced at identical point size rather than shrunk along
    with the plotting boxes. All words and numerical tick labels are retained.
    """
    source=LAYOUT/'Fig07_Community_Typology_and_Hotspots.pdf'
    doc=fitz.open();page=doc.new_page(width=185*MM,height=229*MM)
    edits=[]
    with fitz.open(source) as src:
        for oldtop,oldheight,newtop,newheight in [(1,110.0824,3,86),
                                                 (114,72.3071,92,59),
                                                 (192,75,154,75)]:
            clip=fitz.Rect(0,oldtop*MM,185*MM,(oldtop+oldheight)*MM)
            dest=fitz.Rect(0,newtop*MM,185*MM,(newtop+newheight)*MM)
            page.show_pdf_page(dest,src,0,clip=clip,keep_proportion=False)
            scale=newheight/oldheight
            for block in src[0].get_text('dict',clip=clip)['blocks']:
                if 'lines' not in block:continue
                for line in block['lines']:
                    direction=line['dir']
                    for span in line['spans']:
                        if not span['text'].strip():continue
                        x,y=span['origin']
                        edits.append((span,x,newtop*MM+(y-oldtop*MM)*scale,direction))
    # Remove compressed glyphs without erasing graphics or raster components.
    for b in page.get_text('dict')['blocks']:
        if 'lines' in b:
            for line in b['lines']:
                for s in line['spans']:
                    page.add_redact_annot(fitz.Rect(s['bbox']),fill=False)
    page.apply_redactions(images=0,graphics=0)
    page.insert_font(fontname='ArialReview',fontfile='C:/Windows/Fonts/arial.ttf')
    page.insert_font(fontname='ArialReviewBold',fontfile='C:/Windows/Fonts/arialbd.ttf')
    for span,x,y,direction in edits:
        angle=int(round(-np.degrees(np.arctan2(direction[1],direction[0]))))%360
        assert angle in (0,90,180,270),direction
        rgb=span['color'];color=((rgb>>16&255)/255,(rgb>>8&255)/255,(rgb&255)/255)
        page.insert_text((x,y),span['text'],fontsize=span['size'],rotate=angle,
                         color=color,fontname='ArialReviewBold' if 'Bold' in span['font'] else 'ArialReview')
    p=OUT/'Fig07_Native_Panel_Reflow.pdf';doc.save(p,garbage=4,deflate=True);doc.close()
    with fitz.open(p) as after,fitz.open(source) as before:
        # Whitespace layout may change, but every text word/number must match.
        # Full Arial Unicode embedding extracts the same hyphen glyph as a
        # soft hyphen; normalize that encoding-only difference for comparison.
        words=lambda d:sorted(w[4].replace('\u00ad','-') for w in d[0].get_text('words'))
        assert words(after)==words(before),'Fig07 wording or tick values changed'
    export(p)
    CAPTIONS[p.stem]=str(pd.read_csv(LAYOUT/'FIGURE_V2_1_LAYOUT_INDEX.csv').set_index('figure_stem').loc[
                   'Fig07_Community_Typology_and_Hotspots','caption'])+(
                   ' This layout-only alternative reduces the plot-box heights of the existing '
                   'distribution/profile rows while restoring every text span at its original point '
                   'size. The map row remains at native size. All existing words, ticks, density '
                   'paths, profile values, cluster colors and top-10 boundaries are preserved; '
                   'no distribution fit, cluster, PCA or map calculation is rerun.')

def side_by_side():
    doc=fitz.open();page=doc.new_page(width=420*MM,height=297*MM)
    page.insert_font(fontname='ArialLocal',fontfile='C:/Windows/Fonts/arial.ttf')
    for i,stem in enumerate(['Fig06_Previous_Two_Level_Comparison','Fig06_Preferred_Resource_Policy_Contrasts']):
        x=(15+205*i)*MM
        page.insert_text((x,20*MM),('Previous: absolute outcomes, two crew levels' if i==0 else
                    'Preferred review: policy contrasts, complete tested levels'),fontsize=10,fontname='ArialLocal')
        with fitz.open(OUT/(stem+'.pdf')) as src:
            rect=fitz.Rect(x,30*MM,x+185*MM,30*MM+src[0].rect.height)
            page.show_pdf_page(rect,src,0)
        text=('The old figure mixes resource-driven baseline changes with policy differences. '
              'It omits 86/114 crews and every duration condition.' if i==0 else
              'The candidate isolates Vulnerability-first minus Hospital-first / Impact-first. '
              'The three outcomes distinguish group benefit, aggregate loss and absolute separation. '
              'Reference-specific signs and nonmonotonic cases remain visible.')
        page.insert_textbox(fitz.Rect(x,215*MM,x+185*MM,270*MM),text,fontsize=9,fontname='ArialLocal')
    p=OUT/'FIG06_SIDE_BY_SIDE_REVIEW.pdf';doc.save(p);doc.close();export(p)
    CAPTIONS[p.stem]='A3 landscape comparison at native 185-mm artwork width. Review sheet only; not submission artwork.'

def page_packet():
    doc=fitz.open()
    for stem,caption in CAPTIONS.items():
        if 'SIDE_BY_SIDE' in stem:continue
        with fitz.open(OUT/(stem+'.pdf')) as src:
            h=src[0].rect.height
            page=doc.new_page(width=210*MM,height=max(297*MM,h+90*MM))
            page.insert_font(fontname='ArialLocal',fontfile='C:/Windows/Fonts/arial.ttf')
            page.insert_text((12.5*MM,11*MM),stem.replace('_',' '),fontname='ArialLocal',fontsize=8)
            page.show_pdf_page(fitz.Rect(12.5*MM,18*MM,197.5*MM,18*MM+h),src,0)
            bottom=page.rect.height-10*MM
            excess=page.insert_textbox(fitz.Rect(12.5*MM,25*MM+h,197.5*MM,bottom),caption,
                           fontname='ArialLocal',fontsize=8,lineheight=1.15)
            if excess<0:raise ValueError('Caption overflow: '+stem)
            page.get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(str(OUT/(stem+'_page_preview.png')))
    doc.save(OUT/'RESOURCE_REVIEW_PACKET.pdf');doc.close()

def verify_unchanged():
    before=json.loads((OUT/'BEFORE_STATE.json').read_text())
    science=[p for p,h in before['scientific_hashes'].items() if sha(ROOT/p)!=h]
    publication=[p for p,h in before['publication_hashes'].items() if sha(ROOT/p)!=h]
    assert not science and not publication,(science,publication)
    pd.DataFrame(QA).to_csv(OUT/'NEW_ACTUAL_PDF_MEASUREMENTS.csv',index=False)
    for q in QA:
        assert q['min_text_pt']>=6.99 and not q['off_page_text'],q
        assert 'DejaVu' not in q['fonts'],q
    (OUT/'VALIDATION.json').write_text(json.dumps({'science_source_hash_changes':len(science),
             'publication_figure_changes':len(publication), 'new_figure_promotion':False,
             'bootstrap_or_scientific_execution':False,
             'saved_mean_max_parity_error':pd.read_csv(OUT/'SAVED_VALUE_PARITY.csv').saved_mean_parity_error.max(),
             'author_acceptance':'NOT IMPLIED BY VALIDATION'},indent=2))

if __name__=='__main__':
    effects,raw=read_inputs()
    preferred(effects)
    separation_detail(effects)
    exact_comparison_copies()
    fix_fig05()
    improve_policy_and_cluster_visibility()
    correct_supplement_wording()
    compact_native_fig07()
    side_by_side()
    page_packet()
    (OUT/'CAPTIONS.md').write_text('\n\n'.join('## '+k+'\n\n'+v for k,v in CAPTIONS.items()),encoding='utf-8')
    verify_unchanged()
    print('Review artwork generated; no promotion and no scientific execution.')
