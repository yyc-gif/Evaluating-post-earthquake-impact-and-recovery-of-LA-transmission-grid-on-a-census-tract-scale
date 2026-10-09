"""Native-artwork edits for shared policy legend and explicit typology N/A.

Uses existing vector paths; does not evaluate or alter scientific results.
"""
from pathlib import Path
import csv,hashlib,json,re,shutil,subprocess,tempfile
import fitz
import pandas as pd
from la_grid.paths import REPO_ROOT
from la_grid.plotting import apply_coauthor_figure_feedback as common
from la_grid.plotting.apply_outcome_display_feedback import fonts,sha,text,update_csv
from la_grid.plotting.apply_map_metric_identity_feedback import packets

ROOT=REPO_ROOT;REVIEW=ROOT/'results/figure_review';MM=72/25.4
BASE='63f6ab0daf23ac89bfdeee973b003dc7c177e4ff'
TEMP=Path(tempfile.gettempdir())/'la_minor_legend_20261008'
GENERATOR=Path(__file__).relative_to(ROOT).as_posix()
common.BASE_COMMIT=BASE;common.TEMP=TEMP

def spans(page):
    return [s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]

def replace_text(page,old,new,center=False):
    targets=[s for s in spans(page) if s['text']==old]
    assert len(targets)==1,(old,len(targets))
    s=targets[0];r=fitz.Rect(s['bbox']);origin=s['origin'];size=s['size']
    page.draw_rect(r,color=None,fill=(1,1,1));fonts(page)
    x=(r.x0+r.x1)/2 if center else origin[0]
    text(page,x/MM,origin[1]/MM,new,size,False,center)

def remove_service_loss_ranges(doc):
    # Preserve the original byte stream: serializing CID-font text through a
    # generic PDF parser can change text spacing. Only paint operators change.
    number=rb'[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
    token=re.compile(rb'(?P<rgb>'+number+rb'\s+'+number+rb'\s+'+number+rb'\s+RG)'
        rb'|(?P<gray>'+number+rb'\s+G)'
        rb'|(?P<op>(?<![/A-Za-z0-9])(?:q|Q|S|B)\b)')
    total={'S':0,'B':0};modified=[]
    for x in range(1,doc.xref_length()):
        if not doc.xref_is_stream(x):continue
        raw=doc.xref_stream(x)
        if not re.search(rb'(?:\.188|0\.188)',raw):continue
        active=False;stack=[];removed={'S':0,'B':0}
        def replace(m):
            nonlocal active
            if m.lastgroup=='rgb':
                active=all(abs(float(v)-.1882)<.0002 for v in m.group().split()[:3])
            elif m.lastgroup=='gray':active=abs(float(m.group().split()[0])-.1882)<.0002
            else:
                op=m.group('op')
                if op==b'q':stack.append(active)
                elif op==b'Q':active=stack.pop()
                elif active and op in [b'S',b'B']:
                    removed[op.decode()]+=1;return b'n'
            return m.group()
        updated=token.sub(replace,raw)
        if any(removed.values()):
            assert removed=={'S':27,'B':54},removed
            # All other geometry, color, text and clipping bytes are untouched.
            assert len(updated)==len(raw)
            assert sum(a!=b for a,b in zip(raw,updated))==81
            doc.update_stream(x,updated);modified.append(x)
            for k,v in removed.items():total[k]+=v
    assert len(modified)==1 and total=={'S':27,'B':54},(modified,total)
    return total

def fig04():
    doc,before=common.baseline('Main/Fig04');removed=remove_service_loss_ranges(doc)
    replace_text(doc[0],'Means and 5th-95th realization ranges',
                 'Means; T80 ranges: 5th-95th percentiles',True)
    out=fitz.open();page=out.new_page(width=doc[0].rect.width,height=doc[0].rect.height)
    # Native clipping and translation: no scale change, no chart rerender.
    for source,target in [((25,89,185,112),(25,1,185,24)),
                          ((0,0,185,86),(0,27,185,113)),
                          ((0,115,185,205),(0,115,185,205))]:
        page.show_pdf_page(fitz.Rect(*(v*MM for v in target)),doc,0,
                           clip=fitz.Rect(*(v*MM for v in source)))
    doc.close()
    return common.finish(out,'Main/Fig04',{'before_sha256':before,
        'change':'Grouped policy legend above A, shared by recovery curves and T80 outcomes; service-loss bars retain means only; T80 intervals remain.',
        'deleted_range_paint_operators':removed,'data_values_changed':False,
        'figure_dimensions_changed':False,'curve_scale_changed':False})

def fig07():
    p=ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/stage7_typology_noneligible_tracts.csv'
    d=pd.read_csv(p);assert len(d)==24
    zero=d.formal_population.eq(0);nonzero=~zero
    assert zero.sum()==16 and nonzero.sum()==8
    assert d.loc[nonzero,'Housing_Units_Total'].eq(0).all()
    doc,before=common.baseline('Main/Fig07')
    replace_text(doc[0],'N/A (24)','N/A (No residential typology)')
    return common.finish(doc,'Main/Fig07',{'before_sha256':before,
        'change':'Explicit N/A meaning without falsely describing all excluded tracts as having no residents.',
        'source_table':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),
        'noneligible_tracts':24,'zero_formal_population_tracts':16,
        'positive_population_zero_housing_tracts':8,
        'map_geometry_and_membership_changed':False})

def integrate(records):
    changed={r['file']:r for r in records}
    def index(row):
        key=Path(row['source_path']).relative_to(Path('results/figure_review')).with_suffix('.pdf').as_posix()
        if key in changed:
            p=ROOT/row['source_path'];shutil.copy2(p,ROOT/'results/figures'/row['file'])
            row.update(generator=GENERATOR,sha256_or_lfs_oid='sha256:'+sha(p),
                notes='Shared top policy legend, mean-only service-loss bars and explicit residential-typology N/A label.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    def manifest(row):
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key in changed:
            p=REVIEW/row['final_name'];r=changed[key]
            pointer=subprocess.check_output(['git','show',BASE+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT)
            before=re.search(rb'oid sha256:([0-9a-f]{64})',pointer).group(1).decode()
            row.update(source_commit='MINOR_LEGEND_UPDATE_20261008',sha256=sha(p),
                source_file=p.relative_to(ROOT).as_posix(),current_source_file=p.relative_to(ROOT).as_posix(),
                parent_source_commit=BASE,parent_source_file=p.relative_to(ROOT).as_posix(),parent_sha256=before,
                size_mm='%.3f x %.3f'%tuple(r['size_mm']),min_font_pt=f"{r['min_font_pt']:.3f}")
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    c=subprocess.check_output(['git','show',BASE+':results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md'],cwd=ROOT).decode('utf-8')
    c=c.replace('Impact-first, Hospital-first, Degree-first, Vulnerability-first and Unconstrained use stronger strokes; the remaining policies remain visible with lower opacity.',
                'Impact-first, Hospital-first, Degree-first, Vulnerability-first and Unconstrained use stronger strokes; the other scheduled policies are fully opaque in a separate same-scale view.')
    c=c.replace('whiskers show 5th\u201395th realization ranges, not confidence intervals.',
                'the left service-loss graph shows means without realization-range lines. The right T80 graph retains its 5th-95th realization ranges, not confidence intervals.')
    c=c.replace('Infrastructure-based, community/equity-informed and baseline legend groups describe rule construction;',
                'The grouped policy legend above A is shared by A and the right-hand T80 graph in B. Infrastructure-based, community/equity-informed and baseline legend groups describe rule construction;')
    c=c.replace('including 24 not-applicable tracts shown in gray as N/A rather than as zero or low vulnerability.',
                'including 24 not-applicable tracts shown in gray as N/A (No residential typology), rather than as zero or low vulnerability. Sixteen have zero formal population; eight have positive population but no housing units, so their residential housing feature is undefined. N/A does not mean that every excluded tract has no residents.')
    (REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md').write_text(c,encoding='utf-8',newline='\n');packets(c)
    (REVIEW/'ALL_SUPPLEMENT_FIGURES.pdf').write_bytes((TEMP/'ALL_SUPPLEMENT_FIGURES_baseline.pdf').read_bytes())
    p=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';a=json.loads(p.read_text(encoding='utf-8'))
    a['current_code_files']=[r for r in a['current_code_files'] if r['path']!=GENERATOR]+[{'path':GENERATOR,
        'sha256':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'tracked_in_current_git':True}]
    p.write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8',newline='\n')
    p=ROOT/'docs/reproducibility/MINOR_FIGURE_LEGEND_FEEDBACK_20261008.json'
    p.write_text(json.dumps({'base_commit':BASE,'figures':records,'scientific_content_changed':False},indent=2)+'\n',encoding='utf-8',newline='\n')

def main():
    TEMP.mkdir(exist_ok=True);book,_=common.baseline('ALL_SUPPLEMENT_FIGURES');book.close()
    integrate([fig04(),fig07()])
    print('Two minor figure corrections complete; no scientific stage invoked.')

if __name__=='__main__':main()
