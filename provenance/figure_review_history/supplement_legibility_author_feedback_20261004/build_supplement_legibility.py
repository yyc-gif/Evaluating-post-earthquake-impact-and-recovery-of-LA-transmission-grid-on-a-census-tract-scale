"""S03/S04/S06 author corrections using existing results and vector artwork.

Only presentation is executed. No damage, sampling, scheduling, optimization,
clustering, bootstrap or capacity computation is invoked.
"""
from pathlib import Path
import importlib.util
import hashlib
import json
import re
import shutil

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import geopandas as gpd
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
BUNDLE=ROOT/'results/figure_review/final_submission_candidate_20261002'
MM=72/25.4

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

h=load('supplement_native_export',ROOT/'results/figure_review/supplement_author_feedback_20261004/build_supplement_feedback.py')
h.OUT=OUT
meeting=h.load('existing_map_and_mapping_display',ROOT/'src/la_grid/plotting/build_meeting_figure_collection.py')
STEMS=['FigS03','FigS04','FigS06']
CAPTIONS={}
PARITY=[]

def before_guard():
    path=OUT/'BEFORE_HASH_GUARD.json'
    if path.exists():return json.loads(path.read_text())
    previous=json.loads((ROOT/'results/figure_review/clarity_author_feedback_20261004/BEFORE_HASH_GUARD.json').read_text())
    guard={
        'science':{name:h.sha(ROOT/name) for name in previous['science']},
        'publication':{name:h.sha(ROOT/name) for name in previous['publication']},
        'protected_review':{file.relative_to(ROOT).as_posix():h.sha(file)
            for folder in ['Main','Supplement'] for file in (BUNDLE/folder).glob('*')
            if file.is_file() and file.stem not in STEMS},
    }
    path.write_text(json.dumps(guard,indent=2));return guard

def s03():
    for file in (ROOT/'Data').glob('LA_Tracts_With_Population.*'):h.track(file)
    tracts=meeting.tract_geometry()
    nodes=pd.read_csv(h.track(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv'),dtype={'id':str})
    bases=pd.read_csv(h.track(ROOT/'Data/stage45_active_crew_bases_C57.csv'))
    bases=bases[bases.integer_crews.gt(0)].copy()
    points=meeting.map_points(nodes,tracts.crs)
    origins=gpd.GeoDataFrame(bases,geometry=gpd.points_from_xy(bases.longitude,bases.latitude),
                             crs='EPSG:4326').to_crs(tracts.crs)
    colors={'LADWP':'#377eb8','SCE':'#d95f02'}
    fig=plt.figure(figsize=(185/25.4,118/25.4))
    ax=fig.add_axes([.035,.12,.93,.81]);meeting.draw_tract_base(ax,tracts)
    ax.scatter(points.geometry.x,points.geometry.y,s=11,c='#76838e',alpha=.85,
        edgecolors='white',linewidths=.25,zorder=3)
    for utility,group in origins.groupby('utility'):
        ax.scatter(group.geometry.x,group.geometry.y,s=34,c=colors[utility],
            edgecolors='white',linewidths=.4,zorder=4)
    ax.set_title('A. Origins',loc='left',fontsize=9.5,fontweight='bold',pad=5)
    # Exact downtown coordinates are enlarged in a separate geographic view,
    # never jittered or displaced in the study-area map.
    downtown=origins[origins.yard_id.isin(['D01','D02','D03','D05','D06'])]
    assert len(downtown)==5 and len(origins)==11
    x0,y0,x1,y1=downtown.total_bounds
    padx=(x1-x0)*.23;pady=(y1-y0)*.18
    extent=(x0-padx,x1+padx,y0-pady,y1+pady)
    inset=fig.add_axes([.72,.655,.25,.25])
    tracts.plot(ax=inset,facecolor='#f7f7f7',edgecolor='#d2d5d5',linewidth=.2)
    points.plot(ax=inset,color='#76838e',markersize=11,edgecolor='white',linewidth=.25)
    for utility,group in origins.groupby('utility'):
        inset.scatter(group.geometry.x,group.geometry.y,s=34,c=colors[utility],
            edgecolors='white',linewidths=.4,zorder=4)
    inset.set(xlim=extent[:2],ylim=extent[2:]);inset.set_aspect('equal')
    inset.set_xticks([]);inset.set_yticks([])
    inset.set_title('Downtown origins',fontsize=7.5,pad=3)
    for spine in inset.spines.values():spine.set_linewidth(.5);spine.set_edgecolor('#7c858a')
    ax.add_patch(Rectangle((extent[0],extent[2]),extent[1]-extent[0],extent[3]-extent[2],
        facecolor='none',edgecolor='#7c858a',linewidth=.55,zorder=5))
    handles=[Line2D([],[],marker='o',ls='none',color='#76838e',ms=3.8,label='Substations')]
    handles += [Line2D([],[],marker='o',ls='none',color=color,ms=5.7,label=utility+' origin')
                for utility,color in colors.items()]
    fig.legend(handles=handles,frameon=False,ncol=3,fontsize=7.5,
        loc='lower center',bbox_to_anchor=(.5,.026),columnspacing=1.7,handletextpad=.45)
    top=OUT/'_origins_native.pdf';fig.savefig(top);plt.close(fig)
    source=h.track(ROOT/'results/figure_review/supplement_author_feedback_20261004/FigS03.pdf')
    with fitz.open(source) as old,fitz.open(top) as mapdoc:
        page=old[0]
        title=next(s for _,s in h.spans(page) if h.plain(s['text']).startswith('B. Directed'))
        y0=title['bbox'][1]-1.5*MM;height=page.rect.height-y0
        doc=fitz.open();out=doc.new_page(width=185*MM,height=118*MM+height)
        out.show_pdf_page(fitz.Rect(0,0,185*MM,118*MM),mapdoc,0)
        out.show_pdf_page(fitz.Rect(0,118*MM,185*MM,118*MM+height),old,0,
            clip=fitz.Rect(0,y0,185*MM,page.rect.height),keep_proportion=False)
        doc.save(OUT/'FigS03.pdf',garbage=4,deflate=True);doc.close()
    top.unlink();h.export(OUT/'FigS03.pdf')
    PARITY.append(dict(figure='FigS03',origin_coordinates_unchanged=True,
        origin_count=len(origins),station_count=len(points),travel_panel='unchanged native vector crop',
        overview_origin_area_pt2=34,previous_origin_area_pt2=8,downtown_inset=True))
    CAPTIONS['Supplementary Figure S3. Crew origins and directed travel inputs']=(
        '(A) Crew origins from the reference allocation table, classified by utility, and substations '
        'on the study-area tract background. The inset enlarges the geographically adjacent downtown '
        'origins; positions are unchanged and marker size does not encode crew allocation. '
        '(B) Directed task-to-task road-travel times, with rows denoting origins and columns '
        'destinations; values are in hours. These geographic and travel inputs support the '
        'logistics-constrained restoration model and are not resource-response outcomes.')

def s04():
    original=h.save
    def emit(fig,stem):
        height=210;fig.set_size_inches(185/25.4,height/25.4)
        for legend in list(fig.legends):legend.remove()
        positions=[(13,37),(77,36),(130,35)]
        for ax,(top,hh) in zip(fig.axes,positions):
            ax.set_position([24/185,(height-top-hh)/height,155/185,hh/height])
        a,b,c=fig.axes
        a.get_legend().remove()
        a.legend(frameon=False,ncol=3,fontsize=7.5,loc='upper right',
            handlelength=2.3,handletextpad=.45,columnspacing=1.0)
        emphasized=h.KEYS[:4]+['unconstrained']
        for ax in [b,c]:
            for key,line in zip(h.KEYS,ax.lines):
                line.set_marker('');line.set_alpha(1 if key in emphasized else .27)
                line.set_linewidth(1.5 if key in emphasized else .75)
                line.set_zorder(5 if key in emphasized else 2)
        # The restoration-policy legend belongs to B/C and sits below C,
        # not between A's x-axis and B's title.
        for keys,top,columns in [(emphasized,187,5),([k for k in h.KEYS if k not in emphasized],195,4)]:
            handles=[Line2D([],[],color=h.COLOR[k],ls=h.LINE[k],lw=1.5 if k in emphasized else .75,
                alpha=1 if k in emphasized else .38,label=h.LABEL[k]) for k in keys]
            key=fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(102/185,1-top/height),
                frameon=False,ncol=columns,fontsize=7.5,columnspacing=1.0,handletextpad=.4,handlelength=2.2)
            for k,t in zip(keys,key.get_texts()):t.set_weight('bold' if k in emphasized else 'normal')
        fig.text(102/185,1-182/height,'Restoration policies in B and C',ha='center',fontsize=7.5)
        return original(fig,stem)
    h.save=emit
    try:h.s04()
    finally:h.save=original
    CAPTIONS['Supplementary Figure S4. Static network criticality and dynamic network recovery']=h.CAPTIONS['S4']
    PARITY.append(dict(figure='FigS04',policies_retained=h.KEYS,curve_values_unchanged=True,
        decorative_markers_removed=True,restoration_key_belongs_to='B/C',restoration_key_location='below C'))

def s06():
    original=h.save
    def emit(fig,stem):
        a,b,c=fig.axes
        b.set_title('B. Comparison with SCE records',loc='left',fontweight='bold')
        for text in list(b.texts):text.remove()
        shown=[]
        for line in b.lines:
            if line.get_marker() not in ['o','D']:continue
            x,y=float(line.get_xdata()[0]),float(line.get_ydata()[0])
            baseline=matplotlib.colors.to_hex(line.get_color())=='#8d989f'
            b.annotate(f'{x:.1f}%',(x,y),xytext=(0,-5.5 if baseline else 5.5),textcoords='offset points',
                ha='center',va='top' if baseline else 'bottom',fontsize=7.5,color=line.get_color())
            shown.append([x,y])
        assert len(shown)==6
        b.set_ylim(-.4,2.4)
        b.set_xlabel('Comparable tracts matched (%)',fontsize=8.5)
        c.set_title('C. Tract-level differences between the two mappings',loc='left',fontweight='bold')
        c.set_xlabel('Magnitude of the mean service-loss difference (h)',fontsize=8.5)
        for text in c.texts:
            text.set_text('246 tracts differ\nby more than 1 h')
        PARITY.append(dict(figure='FigS06',point_values=shown,mapping_difference_values_unchanged=True,
            percent_label_gap_pt=5.5,comparable_tract_denominator=337))
        return original(fig,stem)
    h.save=emit
    try:h.s06(meeting)
    finally:h.save=original
    CAPTIONS['Supplementary Figure S6. Mapping support and sensitivity']=(
        '(A) Hospital-first population-weighted service-loss differences under 2pc50 across mapping '
        'cutoffs, relative to the 3% production cutoff. (B) The distance-based baseline and '
        'utility-compatible mapping are compared with SCE substation records for the same 337 '
        'comparable tracts. Any positive-weight assignment matches 320/337 versus 329/337 tracts; '
        'the highest-weight assignment matches 296/337 versus 302/337; and the three highest-weight '
        'assignments match 317/337 versus 324/337. Top candidates are ranked by mapping weight, '
        'not by a general nearest-site rule. This is supporting agreement, not accuracy, feeder '
        'validation or service-territory ground truth. (C) For each tract, the magnitude of the '
        'difference in mean modeled service loss obtained using utility-compatible versus '
        'distance-based mapping, under the same 2pc50 Hospital-first condition. The curve gives '
        'the cumulative share of tracts at or below each difference. Of 2,315 tracts, 246 have a '
        'difference greater than 1 h. This identifies where outcome attribution is sensitive '
        'to the dependency mapping; it is not a policy comparison, a measured prediction error, '
        'or evidence that the mapped electricity supply is known. Service-loss integrals cover 0–480 h.')

def package():
    captions=(BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    for title,body in CAPTIONS.items():
        prefix=title.split('.')[0]
        regex=r'(?ms)(^## '+re.escape(prefix)+r'\.[^\n]*\n\n).*?(?=^## |\Z)'
        captions,n=re.subn(regex,lambda m:'## '+title+'\n\n'+body+'\n\n',captions);assert n==1,title
    (BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').write_text(captions.rstrip()+'\n',encoding='utf-8')
    manifest=pd.read_csv(BUNDLE/'FIGURE_MANIFEST.csv',dtype=str).fillna('')
    for stem in STEMS:
        with fitz.open(OUT/(stem+'.pdf')) as doc:
            pg=doc[0];size=f'{pg.rect.width/MM:.3f} x {pg.rect.height/MM:.3f}'
            minimum=min(span['size'] for _,span in h.spans(pg))
        for ext in ['.pdf','.png']:
            src=OUT/(stem+ext);dst=BUNDLE/'Supplement'/(stem+ext)
            shutil.copyfile(src,dst);assert h.sha(src)==h.sha(dst)
            mask=manifest.final_name.eq(dst.relative_to(BUNDLE).as_posix());assert mask.sum()==1
            manifest.loc[mask,['source_file','source_commit','sha256','size_mm','min_font_pt','status']]=[
                src.relative_to(ROOT).as_posix(),'ARTWORK_COMMIT_PENDING',h.sha(dst),size,f'{minimum:.3f}',
                'AUTHOR_REVIEW_UPDATE_NOT_PROMOTED']
    manifest.to_csv(BUNDLE/'FIGURE_MANIFEST.csv',index=False)
    main=[BUNDLE/f'Main/Fig{i:02d}.pdf' for i in range(1,8)]
    supp=[BUNDLE/f'Supplement/FigS{i:02d}.pdf' for i in range(1,14)]
    book=fitz.open()
    for path in supp:
        with fitz.open(path) as doc:book.insert_pdf(doc)
    book.save(BUNDLE/'ALL_SUPPLEMENT_FIGURES.pdf',garbage=4,deflate=True);book.close()
    matches=list(re.finditer(r'(?m)^## (.+)\n\n',captions));lookup={}
    for i,match in enumerate(matches):
        title=match.group(1);body=captions[match.end():matches[i+1].start() if i+1<len(matches) else len(captions)].strip()
        if title.startswith('Figure '):key=f"Main/Fig{int(title.split('.')[0].replace('Figure ','')):02d}.pdf"
        elif title.startswith('Supplementary Figure S'):key=f"Supplement/FigS{int(title.split('.')[0].replace('Supplementary Figure S','')):02d}.pdf"
        else:continue
        lookup[key]=(title,body)
    book=fitz.open()
    for path in main+supp:
        with fitz.open(path) as doc:book.insert_pdf(doc)
        title,body=lookup[path.relative_to(BUNDLE).as_posix()]
        page=book.new_page(width=185*MM,height=350*MM)
        page.insert_font(fontname='ArialPacket',fontfile=h.ARIAL)
        page.insert_font(fontname='ArialPacketBold',fontfile=h.BOLD)
        page.insert_text((14*MM,20*MM),title,fontname='ArialPacketBold',fontsize=9.5)
        assert page.insert_textbox(fitz.Rect(14*MM,29*MM,171*MM,333*MM),body,fontname='ArialPacket',
            fontsize=9.2,lineheight=1.22)>=0,title
    assert len(book)==40
    book.save(BUNDLE/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()

def main():
    guard=before_guard();h.style()
    for name,fun in [('S03',s03),('S04',s04),('S06',s06)]:
        print('Rendering '+name,flush=True);fun()
    package()
    for category,rows in guard.items():assert all(h.sha(ROOT/path)==sha for path,sha in rows.items()),category
    assert all(h.sha(ROOT/path)==sha for path,sha in h.INPUT_HASHES.items())
    pd.DataFrame(h.QA).to_csv(OUT/'OUTPUT_QA.csv',index=False)
    (OUT/'DISPLAY_PARITY.json').write_text(json.dumps(PARITY,indent=2))
    (OUT/'READ_INPUT_HASHES.json').write_text(json.dumps(h.INPUT_HASHES,indent=2))
    print('PRESENTATION_COMPLETE_SCIENTIFIC_HASH_CHANGES_0',flush=True)

if __name__=='__main__':main()
