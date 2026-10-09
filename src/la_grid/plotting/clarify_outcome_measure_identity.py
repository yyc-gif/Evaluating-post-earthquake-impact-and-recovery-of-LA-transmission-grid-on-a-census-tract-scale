"""Clarify the framework outcome measures and current artwork identities.

Presentation only: reuse native graph vertices and existing result artwork.
Do not evaluate any scientific model or change any scientific table.
"""
from pathlib import Path
import copy,hashlib,json,re,shutil,subprocess,tempfile
import fitz
from la_grid.paths import REPO_ROOT
from la_grid.plotting import apply_coauthor_figure_feedback as common
from la_grid.plotting.apply_outcome_display_feedback import fonts,text,sha,update_csv,tint_green
from la_grid.plotting.apply_map_metric_identity_feedback import CLUSTER_COLORS,packets
from la_grid.plotting.refine_policy_cluster_presentation import streams,RGB_PATTERN,rgb,near,plain

ROOT=REPO_ROOT;REVIEW=ROOT/'results/figure_review';MM=72/25.4
BASE='4a3e1f0056e487dd62f81b35705d6407d44654b0'
TEMP=Path(tempfile.gettempdir())/'la_outcome_identity_20261008'
GENERATOR=Path(__file__).relative_to(ROOT).as_posix()
OLD={1:'#4f8fb7',2:'#e19243',3:'#6ca274',4:'#c5aa63',5:'#87949e'}
NA_GRAY=.72
common.BASE_COMMIT=BASE;common.TEMP=TEMP

def cluster_paint(doc,na=False):
    """Only categorical paint changes; coordinates and quantitative colors stay."""
    counts={cid:0 for cid in [4,5]};na_counts=0
    for x in streams(doc):
        raw=doc.xref_stream(x)
        def replace(m):
            color=tuple(float(m.group(i)) for i in [1,2,3])
            for cid in [4,5]:
                if near(color,rgb(OLD[cid])):
                    counts[cid]+=1
                    return (' '.join(f'{v:.7f}' for v in rgb(CLUSTER_COLORS[cid]))+' '+m.group(4).decode()).encode()
            return m.group(0)
        updated=RGB_PATTERN.sub(replace,raw)
        if na and b'.815686' in raw:
            # Current map polygons with white N/A fill have this exclusive
            # light-gray edge. Assign their fill; leave all valid score colors.
            updated,n=re.subn(rb'(?<![0-9.])(?:0)?\.815686\d*\s+G\b',
                b'.8156863 G .72 g',updated)
            na_counts+=n
        if updated!=raw:doc.update_stream(x,updated)
    assert all(counts.values()),counts
    if na:
        assert na_counts>=48,na_counts
        page=doc[0];spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
        label=next(s for s in spans if plain(s['text'])=='N/A (24)')
        x,y=label['origin']
        page.draw_rect(fitz.Rect(x-9,y-5.25,x-2.25,y),color=(.4667,)*3,fill=(NA_GRAY,)*3,width=.4)
    return {'categorical_color_operator_counts':counts,'N_A_fill_operator_count':na_counts,
            'cluster_id_palette':CLUSTER_COLORS,'N_A_color':'#b8b8b8' if na else None,
            'quantitative_heatmaps_and_hotspot_scale_changed':False}

def framework():
    key='Main/Fig01';doc,before=common.baseline(key);p=doc[0]
    card=fitz.Rect(94.8*MM,164.2*MM,181.7*MM,216.7*MM)
    p.add_redact_annot(card,fill=(1,1,1));p.apply_redactions(images=0,graphics=0,text=0)
    overlay=fitz.open();a=overlay.new_page(width=p.rect.width,height=p.rect.height);fonts(a)
    blue=(.18,.43,.62)
    a.draw_rect(fitz.Rect(94.8*MM,164.2*MM,181.7*MM,169*MM),color=None,fill=(.91,.95,.98))
    a.draw_circle((97*MM,166.5*MM),1.6*MM,color=None,fill=blue)
    text(a,97,167.5,'5',9.5,True,True,(1,1,1));text(a,99.5,167.8,'Community Outcomes',9.5,True)
    titles=[(110,'Recovery outcomes'),(139,'Distributional effects'),(168,'Spatial patterns')]
    for cx,label in titles:text(a,cx,174,label,7.5,True,True)
    # Small visual examples use actual current result paths, not fabricated
    # lower/higher curves. Miniature chart text is removed and labelled outside.
    figure_sources=[('Main/Fig04',(33,15,179,77),(98,176.7,122,184.5)),
                    ('Main/Fig05',(104,14,181,78),(127,176.7,151,184.5)),
                    ('Main/Fig07',(8,178,85,238),(157,176.7,179,184.5))]
    for source,clip,box in figure_sources:
        native,_=common.baseline(source)
        for x in streams(native):
            raw=native.xref_stream(x)
            new=re.sub(rb'\bBT\b.*?\bET\b',b'',raw,flags=re.S)
            if new!=raw:native.update_stream(x,new)
        tint_green(native)
        a.show_pdf_page(fitz.Rect(*(v*MM for v in box)),native,0,
                       clip=fitz.Rect(*(v*MM for v in clip)))
        native.close()
    columns=[(110,['Service loss (0-480 h)','All + hospital tracts','T80: time to 80%']),
             (139,['Q1-Q4 service loss','Group gap and Gini','Vulnerability-first effects']),
             (168,['Tract-level changes','Community typology','Hotspot score'])]
    for cx,labels in columns:
        for y,label in zip([188,191.5,195],labels):text(a,cx,y,label,7,center=True)
    a.draw_line((98*MM,200*MM),(179*MM,200*MM),color=(.78,.83,.87),width=.4)
    text(a,138.5,204,'Tested conditions',7.5,True,True,blue)
    text(a,138.5,209,'Resources (Fig6): crews and repair duration',7,center=True)
    text(a,138.5,214,'Assumptions (S6, S8): mapping, gates and planning limits',7,center=True)
    # Explicit unique graft name avoids recursive resource enumeration.
    p.wrap_contents()
    assert doc.xref_get_key(p.xref,'Resources/XObject/OutcomeMeasures20261008')[0]=='null'
    p._show_pdf_page(a,overlay=True,matrix=(1,0,0,1,0,0),
        clip=a.rect*~a.transformation_matrix,graftmap=fitz.Graftmap(doc),_imgname='OutcomeMeasures20261008')
    overlay.close()
    return common.finish(doc,key,{'before_sha256':before,'changed_region_mm':[94.8,164.2,181.7,216.7],
        'stages_1_to_4_changed':False,'synthetic_lower_higher_lines_removed':True,
        'measure_roles':['480-h service-loss integral','80% threshold-crossing time','Q1-Q4 loss',
                         'between-group gap','population-weighted Gini','tract spatial effects','typology/hotspots'],
        'condition_checks_sources':['Main/Fig06','Supplement/FigS06','Supplement/FigS08']})

def wording(doc):
    p=doc[0];edits=[]
    for b in p.get_text('dict')['blocks']:
        for line in b.get('lines',[]):
            for s in line['spans']:
                old=plain(s['text']);new=None
                if 'each named reference' in old:
                    new='Vulnerability-first compared with Hospital-first, Impact-first and Degree-first'
                elif 'High-low' in old or 'high-low' in old:
                    # The high/low descriptor is a plain hyphen, not an equation.
                    new=s['text'].replace('High–low','High-low').replace('high–low','high-low')
                if new is not None and new!=s['text']:edits.append((s,line,new))
    for s,line,new in edits:p.add_redact_annot(fitz.Rect(s['bbox']),fill=(1,1,1))
    if edits:p.apply_redactions(images=0,graphics=0,text=0)
    fonts(p)
    for s,line,new in edits:
        bold='Bold' in s['font'];font=fitz.Font(fontfile='C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf')
        rotate=90 if line['dir'][1]<-.5 else 270 if line['dir'][1]>.5 else 0
        origin=fitz.Point(s['origin'])
        if rotate:origin.y=(s['bbox'][1]+s['bbox'][3])/2+font.text_length(new,fontsize=s['size'])/2
        else:origin.x=(s['bbox'][0]+s['bbox'][2]-font.text_length(new,fontsize=s['size']))/2
        color=tuple(((s['color']>>i)&255)/255 for i in [16,8,0])
        p.insert_text(origin,new,fontname='DisplayArialBold' if bold else 'DisplayArial',
                      fontsize=s['size'],color=color,rotate=rotate)
    return [{'old':s['text'],'new':new} for s,line,new in edits]

def secondary_visibility(doc):
    count=0;keys=[]
    # A4 in these precise native Forms controls only secondary recovery strokes,
    # with fill opacity 1. Background/grid and outcome-range states differ.
    for x in streams(doc):
        if doc.xref_get_key(x,'Resources/ExtGState/A4/CA')[1] in ['.25','0.25']:
            assert doc.xref_get_key(x,'Resources/ExtGState/A4/ca')[1]=='1'
            doc.xref_set_key(x,'Resources/ExtGState/A4/CA','.55');keys.append(x)
    # The grouped key is a pale RGB tint, independent of curve alpha.
    for x in streams(doc):
        raw=doc.xref_stream(x)
        def replace(m):
            nonlocal count
            value=tuple(float(m.group(i)) for i in [1,2,3])
            for k in ['centrality-first','betweenness-first','closeness-first','random']:
                c=rgb(common.COLORS[k]);old=tuple(.45*v+.55 for v in c)
                if near(value,old):
                    count+=1;return (' '.join(f'{.55*v+.45:.7f}' for v in c)+' '+m.group(4).decode()).encode()
            return m.group(0)
        new=RGB_PATTERN.sub(replace,raw)
        if new!=raw:doc.update_stream(x,new)
    return {'recovery_opacity_forms':keys,'secondary_curve_alpha_before':.25 if keys else None,
            'secondary_curve_alpha_after':.55 if keys else None,'secondary_legend_color_operator_count':count,
            'all_eight_scheduled_policies_preserved':True,'all_path_vertices_preserved':True}

def integrate(records):
    changed={r['file']:r for r in records}
    def index(row):
        path=ROOT/row['source_path'];key=path.relative_to(REVIEW).with_suffix('.pdf').as_posix()
        if key in changed:
            shutil.copy2(path,ROOT/'results/figures'/row['file'])
            row.update(sha256_or_lfs_oid='sha256:'+sha(path),generator=GENERATOR,
                       notes='Explicit outcome measures and references; gray reserved for N/A; synchronized cluster colors; visible secondary policies.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    def manifest(row):
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key in changed:
            r=changed[key];p=REVIEW/row['final_name']
            row.update(source_file=p.relative_to(ROOT).as_posix(),current_source_file=p.relative_to(ROOT).as_posix(),
                source_commit='OUTCOME_MEASURE_IDENTITY_UPDATE_20261008',sha256=sha(p),
                parent_source_commit=BASE,parent_source_file=p.relative_to(ROOT).as_posix(),
                parent_sha256=common.baseline_digest('results/figure_review/'+row['final_name']),
                size_mm='%.3f x %.3f'%tuple(r['size_mm']),min_font_pt=f"{r['min_font_pt']:.3f}",
                status='AUTHOR_REQUESTED_CURRENT_DISPLAY')
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    p=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md'
    c=subprocess.check_output(['git','show',BASE+':results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md'],cwd=ROOT).decode()
    c=c.replace('high–low','high-low').replace('High–low','High-low')
    c=c.replace('including 24 not-applicable tracts shown in white as N/A',
                'including 24 not-applicable tracts shown in gray as N/A')
    c=c.replace('Vulnerability-first relative to the named reference:',
                'Vulnerability-first minus Hospital-first, Impact-first or Degree-first, according to the comparison key:')
    start=c.index('## Figure 1.');end=c.index('## Figure 2.',start)
    block=c[start:end].rstrip()+(' The community-outcome stage separates cumulative service loss, integrated over 0-480 h, from T80, the time to first reach 80% modeled service. '
        'Loss is compared across all tracts, hospital-linked tracts and social-vulnerability quartiles Q1-Q4; group differences, population-weighted Gini and tract-level spatial effects describe different distributional dimensions. '
        'Community typology and hotspot scores describe spatial patterns. Tested crew/duration conditions are shown in Figure 6; dependency/service-gate assumptions and SCE planning-limit checks are shown in Supplementary Figures S6 and S8, rather than being additional community outcome metrics.\n\n')
    c=c[:start]+block+c[end:]
    start=c.index('## Figure 4.');end=c.index('## Figure 5.',start)
    block=c[start:end].rstrip()+(' Here Centrality-first is specifically the network lambda2-impact rule: stations are ranked by the relative reduction in algebraic connectivity after their removal from the initial largest connected component. '
        'It is distinct from degree, betweenness and closeness rankings, and from the population-impact rule Impact-first.\n\n')
    c=c[:start]+block+c[end:];p.write_text(c,encoding='utf-8');packets(c)
    a_path=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';a=json.loads(a_path.read_text())
    registered=[GENERATOR,'src/la_grid/plotting/apply_map_metric_identity_feedback.py']
    for path in registered:
        record={'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
                'tracked_in_current_git':True}
        a['current_code_files']=[r for r in a['current_code_files'] if r['path']!=path]+[record]
    a_path.write_text(json.dumps(a,indent=2)+'\n')
    report={'base_commit':BASE,'figures':records,'cluster_colors':CLUSTER_COLORS,
       'N_A_gray':'#b8b8b8','scientific_stage_invoked':False,'source_tables_changed':False,
       'resource_decision':'Keep the two tested OFAT families in Fig06; mapping/gate/threshold and SCE checks remain separate.',
       'centrality_definition_source':'src/la_grid/core/C257H_Project_Main.py:compute_impact_centrality'}
    (ROOT/'docs/reproducibility/OUTCOME_MEASURE_IDENTITY_UPDATE_20261008.json').write_text(json.dumps(report,indent=2)+'\n')

def main():
    TEMP.mkdir(exist_ok=True);records=[framework()]
    for key in ['Main/Fig04','Main/Fig05','Main/Fig06','Main/Fig07',
                'Supplement/FigS04','Supplement/FigS09','Supplement/FigS12','Supplement/FigS13']:
        print('Updating',key,flush=True);doc,before=common.baseline(key);details={'before_sha256':before}
        if key in ['Main/Fig07','Supplement/FigS09']:details['cluster_display']=cluster_paint(doc,na=key=='Main/Fig07')
        if key in ['Main/Fig04','Supplement/FigS04']:details['policy_visibility']=secondary_visibility(doc)
        details['wording_changes']=wording(doc)
        if not details['wording_changes'] and key not in ['Main/Fig04','Main/Fig07','Supplement/FigS04','Supplement/FigS09']:
            doc.close();continue
        records.append(common.finish(doc,key,details))
    integrate(records);print('Presentation updates complete; scientific stages not run.',flush=True)

if __name__=='__main__':main()
