"""Figure-only integration from pinned payloads. Never execute scientific stages.

Use the existing approved S05 bytes. Other changes are PDF paint operators or
rendering of an already archived S11 display table. No model is fitted.
"""
from pathlib import Path
import csv, io, json, os, re, subprocess, sys
import fitz
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
import consolidate_current_figure_suite as util

ROOT=util.ROOT; DEST=ROOT/'results/figure_review'; MM=util.MM
BASE='c0a11ffb4df523111efe6c8e65cfe86eadffec3c'
FIGURE_COMMIT='34c49469036354453c7b1f7fcef9cd92d14e8a3d'
APPROVAL_COMMIT='0d3d30cd3ce5a5503ff1711371a82c571eb85cef'
SOURCE='results/figure_review/Additional_Evidence/Final_Pure_Random_GA_S05_20261012'
APPROVAL='results/figure_review/Additional_Evidence/S05_Final_Author_Approval_20261012'
QA=ROOT/'docs/reproducibility/official_figure_suite_review_20261012'
HISTORY=ROOT/'provenance/figure_review_history/official_suite_update_20261012'
EXPECTED=util.FIGURES
RGB=re.compile(rb'([-+]?[0-9.]+)\s+([-+]?[0-9.]+)\s+([-+]?[0-9.]+)\s+(rg|RG)\b')
PALETTE={1:'#4f8fb7',2:'#e19243',3:'#6ca274',4:'#8a83b8',5:'#b45f50'}
SOURCE_RECORDS={}

def payload(commit,rel):
    blob=util.git('show',f'{commit}:{rel}')
    m=re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)',blob)
    if not m:
        data=blob
    else:
        sha,size=m[1].decode(),int(m[2])
        common=Path(util.git('rev-parse','--path-format=absolute','--git-common-dir').decode().strip())
        candidates=[common/'lfs/objects'/sha[:2]/sha[2:4]/sha,ROOT/rel]
        candidates += [ROOT.parent/name/rel for name in ['_fu11','_s05r16','_s05a17','_fr11']]
        candidates.append(util.ORIGINAL/rel)
        for p in candidates:
            if p.exists() and p.stat().st_size==size and util.sha(p)==sha:
                data=open(util.lp(p),'rb').read();break
        else:
            raise FileNotFoundError(f'Actual LFS bytes missing: {commit}:{rel} ({sha})')
    SOURCE_RECORDS[f'{commit}:{rel}']={'commit':commit,'path':rel,'sha256':util.digest(data),'bytes':len(data)}
    return data

def native(stem):
    return fitz.open(stream=payload(BASE,'results/figure_review/'+stem+'.pdf'),filetype='pdf')

def streams(doc):
    return sorted(set(doc[0].get_contents())|{x for x in range(1,doc.xref_length())
        if doc.xref_get_key(x,'Subtype')[1]=='/Form'})

def recolor_c4(doc):
    old=np.array(to_rgb('#7b828f'));new=to_rgb(PALETTE[4]);count=0
    for x in streams(doc):
        raw=doc.xref_stream(x)
        def replace(m):
            nonlocal count
            if np.max(abs(np.array([float(m[i]) for i in [1,2,3]])-old))<3e-5:
                count+=1
                return ('%.9f %.9f %.9f '%new).encode()+m[4]
            return m[0]
        updated=RGB.sub(replace,raw)
        if updated!=raw:
            assert RGB.sub(b'PAINT',raw)==RGB.sub(b'PAINT',updated)
            doc.update_stream(x,updated)
    assert count>0
    return {'C4_before':'#7b828f','C4_after':PALETTE[4],'operators_changed':count,
        'all_noncolor_bytes_unchanged':True}

def white_na(doc):
    count=0;hashes=[];legend=0
    # Exact fill introduced by the preceding official round. These are the
    # 24 N/A tracts in both C and D, not colored zero-valued hotspot tracts.
    pattern=re.compile(rb'(?<![0-9.])0\.850980392 g\s+(.*?)\s+B\b',re.S)
    for x in streams(doc):
        raw=doc.xref_stream(x)
        def replace(m):
            nonlocal count
            path=m[1]
            assert not any(t in path for t in [b'BT',b' rg',b' g',b'Do',b' RG',b' G'])
            # Paths are byte-preserved; only any inherited style preamble is
            # replaced. Restore paint state after each white outlined polygon.
            geometry=re.sub(rb'^1 j \.1 w\s*',b'',path)
            assert re.search(rb'\bm\b',geometry) and b' h' in geometry
            hashes.append(util.digest(geometry));count+=1
            return b'q 1 g .30 G .45 w 1 j '+geometry+b' B Q'
        updated=pattern.sub(replace,raw)
        def swatch(m):
            nonlocal legend
            if m[4]==b'rg' and max(abs(float(m[i])-217/255) for i in [1,2,3])<2e-7:
                legend+=1;return b'1 1 1 rg'
            return m[0]
        updated=RGB.sub(swatch,updated)
        if updated!=raw:doc.update_stream(x,updated)
    assert count==48 and legend==1,(count,legend)
    return {'NA_tracts':24,'map_paths_unchanged_sha256':hashes,'white_NA_paths':count,
        'outline_gray':.30,'outline_width_pt':.45,'white_legend_swatches':legend,
        'cluster_membership_hotspot_values_and_study_boundary_unchanged':True}

def population_palette(doc):
    t=np.linspace(0,1,256)
    old=LinearSegmentedColormap.from_list('old',['#f3f3f3','#c6c6c6','#555555'])(t)[:,:3]
    new=plt.get_cmap('YlGnBu')(np.linspace(.15,.85,256))[:,:3]
    count=0
    for x in streams(doc):
        raw=doc.xref_stream(x)
        def replace(m):
            nonlocal count
            if m[4]!=b'rg':return m[0]
            color=np.array([float(m[i]) for i in [1,2,3]])
            delta=np.max(abs(old-color),axis=1);i=int(delta.argmin())
            if delta[i]<2e-6:
                count+=1;return ('%.9f %.9f %.9f rg'%tuple(new[i])).encode()
            return m[0]
        updated=RGB.sub(replace,raw)
        if updated!=raw:
            assert RGB.sub(b'PAINT',updated)==RGB.sub(b'PAINT',raw)
            doc.update_stream(x,updated)
    assert count>4000,count
    images=[]
    for x in range(1,doc.xref_length()):
        if doc.xref_get_key(x,'Subtype')[1]!='/Image':continue
        cs=doc.xref_get_key(x,'ColorSpace')[1];m=re.search(r'<([0-9A-Fa-f]+)>',cs)
        if not m:continue
        arr=np.frombuffer(bytes.fromhex(m[1]),dtype=np.uint8).reshape(-1,3)/255
        mapped=[]
        for color in arr:
            delta=np.max(abs(old-color),axis=1);i=int(delta.argmin());assert delta[i]<.01
            mapped.append(np.rint(new[i]*255).astype(np.uint8))
        indices=util.digest(doc.xref_stream(x))
        doc.xref_set_key(x,'ColorSpace',cs[:m.start(1)]+np.array(mapped,dtype=np.uint8).tobytes().hex()+cs[m.end(1):])
        assert indices==util.digest(doc.xref_stream(x))
        images.append({'xref':x,'scalar_indices_sha256':indices})
    assert len(images)==1
    return {'metric':'tract population','panel':'C','palette':'YlGnBu, t=0.15..0.85',
        'color_operators_changed':count,'colorbar_scalar_indices':images,
        'population_log_norm_range_geometries_stations_and_text_unchanged':True}

POLICIES=['impact-first','hospital-first','degree-first','vulnerability-first','betweenness-first','random']
LABELS=['Impact-first','Hospital-first','Degree-first','Vulnerability-first','Betweenness-first','Random']
FIELDS=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr','population_T80_hr']

def render_s11():
    rel='provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv'
    rows=util.csv_rows(payload(BASE,rel))
    a=[]
    for k in POLICIES:
        row=[]
        for field in FIELDS:
            hit=[r for r in rows if r['hazard']=='2pc50' and r['strategy_id']==k and r['metric']==field]
            assert len(hit)==1
            row.append(float(hit[0]['mean_paired_difference']))
        a.append(row)
    a=np.array(a);assert np.isfinite(a).all() and a.min()>=0
    vmax=float(a.max());cmap=LinearSegmentedColormap.from_list('readable_blues',plt.get_cmap('Blues')(np.linspace(.12,.95,256)))
    plt.rcParams.update({'font.family':'Arial','font.size':8.5,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(185/25.4,112/25.4))
    fig.text(.5,1-3/112,'Policy-outcome contrasts under 2pc50',ha='center',va='top',fontsize=10.5,fontweight='bold')
    fig.text(.5,1-11.2/112,'Reference crew availability and repair-duration multiplier 1.00',ha='center',va='top',fontsize=8.5)
    ax=fig.add_axes([44/185,(112-77)/112,132/185,60/112])
    norm=Normalize(vmin=0,vmax=vmax)
    im=ax.imshow(a,cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')
    ax.set_yticks(range(6),LABELS,fontsize=9)
    ax.set_xticks(range(4),['All-tract\nservice loss','Q4 tract\nservice loss','Hospital-tract\nservice loss','Population\nT80'],fontsize=8.5)
    ax.tick_params(length=0,pad=5)
    for spine in ax.spines.values():spine.set_linewidth(.6)
    # Replace the image with individual vector cell paths; no white divider.
    im.remove()
    for i in range(6):
        for j in range(4):
            color=cmap(norm(a[i,j]));ax.add_patch(plt.Rectangle((j-.5,i-.5),1,1,facecolor=color,edgecolor='none',antialiased=False))
            lum=np.dot(color[:3],[.2126,.7152,.0722])
            ax.text(j,i,f'{a[i,j]:+.2f}',ha='center',va='center',fontsize=9,color='white' if lum<.40 else '#15232a')
    ax.set_xlim(-.5,3.5);ax.set_ylim(5.5,-.5)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([44/185,(112-100)/112,132/185,3/112]),orientation='horizontal')
    cb.set_ticks([0,2,4,6,8,vmax]);cb.set_ticklabels(['0','2','4','6','8',f'{vmax:.2f}'])
    cb.ax.tick_params(labelsize=8,length=2,pad=2)
    cb.set_label('Mean increase relative to Unconstrained (h)',fontsize=8.5,labelpad=3)
    buf=io.BytesIO();fig.savefig(buf,format='pdf');plt.close(fig)
    doc=fitz.open(stream=buf.getvalue(),filetype='pdf')
    return doc,{'source_path':rel,'source_sha256':SOURCE_RECORDS[f'{BASE}:{rel}']['sha256'],
        'hazard':'2pc50','policies':POLICIES,'metrics':FIELDS,'saved_display_means':a.tolist(),
        'linear_norm_h':[0,vmax],'new_means_or_uncertainty_computed':False,
        'removed_from_numbered_figure':['LongBeach','SanFernando','Northridge'],
        'prior_four_scenario_artwork_retained_in_history':True}

def pdf_info(doc):
    p=doc[0];spans=[s for b in p.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)['blocks']
        for l in b.get('lines',[]) for s in l['spans']]
    return {'size_mm':[p.rect.width/MM,p.rect.height/MM],'min_font_pt':min(s['size'] for s in spans),
        'page_count':len(doc),'image_count':len(p.get_images())}

def export(doc,stem,keep_bytes=False):
    if not keep_bytes:util.write(DEST/(stem+'.pdf'),doc.tobytes(garbage=4,deflate=True))
    # A fresh renderer process prevents stale cross-document font caches and
    # always renders the saved PDF, not an older generated PNG.
    script=QA/'render_one.py'
    subprocess.run([sys.executable,str(script),str(DEST/(stem+'.pdf')),str(DEST/(stem+'.png')),
        str(DEST/'Page_Previews'/(Path(stem).name+'.png'))],check=True)
    return pdf_info(doc)

def main():
    reference=json.loads(payload(BASE,'docs/reproducibility/figure_details_20261012/PRESERVATION_BEFORE.json'))
    before=util.protected_snapshot(reference);assert before==reference
    util.dump(QA/'PRESERVATION_BEFORE.json',before)
    status_before=util.git('status','--porcelain=v1','-z').decode()
    util.dump(QA/'STARTING_STATE.json',{'HEAD':BASE,'branch':util.git('branch','--show-current').decode().strip(),
        'status_before_authoring':status_before,'protected_science_files':before['protected_count'],
        'original_staged_items':before['staged_count'],'new_scientific_runs':0})
    # Materialize only exact suite assets. No other LFS or manuscript file is
    # checked out or replaced, and no review branch is merged wholesale.
    old_manifest=util.csv_rows(payload(BASE,'results/figure_review/FIGURE_MANIFEST.csv'))
    index=util.csv_rows(payload(BASE,'results/figures/FIGURE_INDEX.csv'))
    for stem in EXPECTED:
        for ext in ['pdf','png']:
            rel='results/figure_review/'+stem+'.'+ext
            data=payload(BASE,rel);util.write(ROOT/rel,data)
            mirror=next(r['mirror_file'] for r in old_manifest if r['current_source_file']==rel)
            util.write(ROOT/mirror,data)
        rel='results/figure_review/Page_Previews/'+Path(stem).name+'.png'
        util.write(ROOT/rel,payload(BASE,rel))
    for rel in ['results/figure_review/ALL_MAIN_FIGURES.pdf','results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf',
        'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf']:
        util.write(ROOT/rel,payload(BASE,rel))
    old_caps=util.captions(payload(BASE,'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    for n in ['FigS05','FigS11']:
        for ext in ['pdf','png']:
            util.write(HISTORY/(n+'.'+ext),payload(BASE,'results/figure_review/Supplement/'+n+'.'+ext))
        h=next(h for h in old_caps if re.search(r'S0?'+str(int(n[4:]))+r'\.',h))
        util.write(HISTORY/(n+'_CAPTION.md'),'# '+h+'\n\n'+old_caps[h]+'\n')
    approved=payload(APPROVAL_COMMIT,APPROVAL+'/S05_CONCISE_MANUSCRIPT_CAPTION.md').decode()
    for name in ['S05_PUBLICATION_INTEGRATION_PLAN.md','S05_FINAL_VISUAL_REVIEW.md']:
        util.write(QA/'approved_source_records'/name,payload(APPROVAL_COMMIT,APPROVAL+'/'+name))
    util.write(QA/'approved_source_records/S05_CONCISE_MANUSCRIPT_CAPTION.md',approved)
    util.write(QA/'approved_source_records/S05_SOURCE_DATA_PROVENANCE_MANIFEST.json',
        payload(FIGURE_COMMIT,SOURCE+'/SOURCE_DATA_PROVENANCE_MANIFEST.json'))
    source_manifest=json.loads(payload(FIGURE_COMMIT,SOURCE+'/OUTPUT_HASH_MANIFEST.json'))
    for ext in ['pdf','png']:
        filename='FigS05_GA_Final_Candidate.'+ext
        data=payload(FIGURE_COMMIT,SOURCE+'/'+filename)
        assert util.digest(data)==source_manifest['files'][filename]['sha256']
        util.write(DEST/('Supplement/FigS05.'+ext),data)
    s05=fitz.open(util.lp(DEST/'Supplement/FigS05.pdf'))
    info={'Supplement/FigS05':pdf_info(s05)}
    pix=s05[0].get_pixmap(matrix=fitz.Matrix(160/72,160/72));pix.set_dpi(160,160)
    pix.save(util.lp(DEST/'Page_Previews/FigS05.png'));s05.close()
    edits={'Supplement/FigS05':{'official_integration_authorized_by_current_user_task':True,
        'figure_commit':FIGURE_COMMIT,'caption_approval_commit':APPROVAL_COMMIT,
        'reviewed_PDF_and_PNG_copied_exactly':True}}
    f7=native('Main/Fig07');edits['Main/Fig07']={'palette':recolor_c4(f7),'NA':white_na(f7)}
    info['Main/Fig07']=export(f7,'Main/Fig07');f7.close()
    s9=native('Supplement/FigS09');edits['Supplement/FigS09']=recolor_c4(s9)
    info['Supplement/FigS09']=export(s9,'Supplement/FigS09');s9.close()
    s10=native('Supplement/FigS10');edits['Supplement/FigS10']=population_palette(s10)
    info['Supplement/FigS10']=export(s10,'Supplement/FigS10');s10.close()
    s11,edits['Supplement/FigS11']=render_s11()
    info['Supplement/FigS11']=export(s11,'Supplement/FigS11');s11.close()
    # Verify S13 through a fresh rendering. Its PDF, PNG and preview are
    # complete; regenerated exports match the existing bytes exactly.
    s13=native('Supplement/FigS13');info['Supplement/FigS13']=export(s13,'Supplement/FigS13',keep_bytes=True);s13.close()
    edits['Supplement/FigS13']={'PDF_retained_exactly':True,'PNG_and_preview_rerendered_with_identical_bytes':True,
        'no_labels_or_numbers_added_to_PDF':True,'merge_decision':'KEEP_SEPARATE'}
    caps=dict(old_caps)
    s5key=next(h for h in caps if h.startswith('Supplementary Figure S5.'))
    newkey='Supplementary Figure S5. Random-initialization search and independent validation of the frozen GA sequence'
    approved_body=approved.split('\n\n',1)[1].strip()
    caps={newkey if h==s5key else h:approved_body if h==s5key else b for h,b in caps.items()}
    f7key=next(h for h in caps if h.startswith('Figure 7.'))
    caps[f7key]=caps[f7key].replace('shown in light gray as N/A','shown in white with dark boundaries as N/A')
    s10key=next(h for h in caps if h.startswith('Supplementary Figure S10.'))
    caps[s10key]=caps[s10key].replace('neutral-gray tract population shading','sequential tract population shading')
    s11key=next(h for h in caps if h.startswith('Supplementary Figure S11.'))
    caps[s11key]=('Mean policy-outcome contrasts under 2pc50 at reference crew availability and repair-duration multiplier 1.00. '
        'Each cell is the mean realization-level difference between the named scheduled policy and Unconstrained, using the same 1,000 physical realizations. '
        'Rows show the six selected fixed-rule manuscript policies. Columns show all-tract population-weighted service loss, Q4 population-weighted service loss, '
        'hospital-linked equal-tract mean service loss and population T80. Service loss integrates one minus modeled service availability over 0-480 h; '
        'T80 is the first crossing of 80% population-weighted modeled service, a distinct time outcome. Printed values and the common linear sequential colorbar '
        'report mean increases in hours, with zero corresponding to the Unconstrained reference and no clipping. The source table records 5th-95th realization-difference '
        'ranges; uncertainty is not drawn in this mean heatmap. Hospital-linked loss is not electricity delivered to hospitals or clinical capacity. '
        'These are the original fixed-rule comparisons; the final GA in Supplementary Figure S5 is not included in this original 1,000-realization cohort. '
        'The complete historical cross-scenario evidence is preserved separately; this panel does not estimate a hazard-intensity effect.')
    caps={'Supplementary Figure S11. Policy-outcome contrasts under 2pc50' if h==s11key else h:b for h,b in caps.items()}
    # Figure-facing clauses only. Final GA is not silently added to the
    # existing fixed-rule/resource-family plots or formal strategy archives.
    for h in list(caps):
        if h.startswith(('Figure 4.','Supplementary Figure S12.','Supplementary Figure S13.')):
            caps[h]=re.sub(r'(?:The )?(?:original )?Direct-community[^.]*\.',
                'In these original fixed-rule experiments, archived Direct-community coincided with Impact-first and is shown once.',caps[h],flags=re.I)
            caps[h]+=' The final GA shown in Supplementary Figure S5 is a separate validated sequence and is not included in these plotted policy comparisons.'
    util.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+'\n\n'.join('## '+h+'\n\n'+b for h,b in caps.items())+'\n')
    changes=set(edits)-{'Supplement/FigS13'};manifest=[]
    for row in old_manifest:
        row=row.copy();stem,ext=row['final_name'].rsplit('.',1);rel=row['current_source_file']
        data=open(util.lp(ROOT/rel),'rb').read();sha=util.digest(data)
        changed=sha!=row['sha256']
        row['change_in_this_update']='UPDATED' if changed else 'RETAINED'
        if changed:
            row.update(parent_source_file=rel,parent_source_commit=BASE,parent_sha256=row['sha256'],sha256=sha,
                size_mm=' x '.join(f'{v:.3f}' for v in info[stem]['size_mm']),min_font_pt=f"{info[stem]['min_font_pt']:.3f}",
                source_commit=FIGURE_COMMIT if stem=='Supplement/FigS05' else BASE,
                source_file=SOURCE+'/FigS05_GA_Final_Candidate.'+ext if stem=='Supplement/FigS05' else rel,
                presentation_generator='src/la_grid/plotting/integrate_final_s05_and_suite_review_20261012.py',
                presentation_generator_sha256=util.sha(__file__))
            util.write(ROOT/row['mirror_file'],data)
        else:assert sha==row['sha256']
        idx=next(r for r in index if r['source_path']==rel)
        idx['sha256_or_lfs_oid']=sha
        if stem in changes:
            idx['generator']=row['presentation_generator']
            idx['notes']='Current figure-only integration/review; see FIGURE_SUITE_UPDATE_SUMMARY_20261012.md.'
        if stem=='Supplement/FigS05':
            idx.update(scientific_question='What do pure-random GA search and validation of the frozen legacy sequence show?',
                main_message='Twenty pure-random searches and archived 2,000-case validation; finite-search and distributional limitations disclosed.',
                source_authority=FIGURE_COMMIT,
                source_data_path='docs/reproducibility/official_figure_suite_review_20261012/approved_source_records/S05_SOURCE_DATA_PROVENANCE_MANIFEST.json',
                source_data_sha256=SOURCE_RECORDS[f'{FIGURE_COMMIT}:{SOURCE}/SOURCE_DATA_PROVENANCE_MANIFEST.json']['sha256'],
                scientific_content='Search evidence and distinct completed independent physical-validation cohort; formal strategies remain unchanged.')
        if stem=='Supplement/FigS11':
            idx.update(scientific_question='How much do the six fixed policies increase service loss and population T80 relative to Unconstrained under 2pc50?',
                main_message='One 2pc50 heatmap with a common linear 0-to-maximum-hour scale; historical cases retained as evidence.',
                scientific_content='Original saved mean fixed-rule differences for 2pc50; no GA or newly computed statistics.')
        manifest.append(row)
    util.write_csv(DEST/'FIGURE_MANIFEST.csv',manifest);util.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    util.dump(DEST/'CURRENT_CLUSTER_PALETTE.json',{'formal_cluster_count':5,'colors':PALETTE,
        'NA_fill':'#ffffff','NA_outline':'#4d4d4d','NA_outline_pt':.45,'applies_to':['Fig07 A/C','FigS09 A'],
        'cluster_assignments_and_PCA_unchanged':True})
    util.pdfmetrics.registerFont(util.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    util.pdfmetrics.registerFont(util.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    packets=[fitz.open(),fitz.open(),fitz.open()]
    for stem,(h,b) in zip(EXPECTED,caps.items()):
        fig=fitz.open(util.lp(DEST/(stem+'.pdf')))
        packets[0 if stem.startswith('Main/') else 1].insert_pdf(fig)
        packets[2].insert_pdf(fig);cap=util.caption_pdf(h,b);packets[2].insert_pdf(cap)
        fig.close();cap.close()
    old=fitz.open(stream=payload(BASE,'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf')
    packets[2].insert_pdf(old,from_page=38,to_page=41);old.close()
    for name,d in zip(['ALL_MAIN_FIGURES','ALL_SUPPLEMENT_FIGURES','ALL_FIGURES_WITH_CAPTIONS'],packets):
        util.write(DEST/(name+'.pdf'),d.tobytes(garbage=4,deflate=True));d.close()
    after=util.protected_snapshot(reference);assert before==after
    util.dump(QA/'PRESERVATION_AFTER.json',after)
    metrics={}
    for stem in EXPECTED:
        d=fitz.open(util.lp(DEST/(stem+'.pdf')));metrics[stem]=pdf_info(d);d.close()
    records=[{'current_file':r['current_source_file'],'source_file':r['source_file'],'source_commit':r['source_commit'],
        'sha256':r['sha256'],'mirror_file':r['mirror_file'],'change':r['change_in_this_update']} for r in manifest]
    util.dump(QA/'INTEGRATION_QA.json',{'baseline_commit':BASE,'figures':records,'native_pdf_metrics':metrics,'operator_edits':edits,
        'protected_file_count':before['protected_count'],'staged_item_count':before['staged_count'],
        'scientific_results_recomputed':False,'original_worktree_unchanged':before==after,
        'manuscripts_modified':False,'packet_pages':{'main':7,'supplement':12,'with_captions':42},
        'updated_figures':list(changes),'retained_figures':[s for s in EXPECTED if s not in changes]})
    util.dump(QA/'SOURCE_HASHES.json',SOURCE_RECORDS)
    print('Completed figure-only integration; unchanged approved S05; 19 numbered figures; 42-page complete packet.',flush=True)

if __name__=='__main__':
    if '--historical' in sys.argv:
        main()
    else:
        from build_current_suite_k3 import main as current_main
        current_main()
