"""Targeted vector edits to the current authority. No scientific stage is run.

Read original PDF operators and frozen metadata. Marker edits wrap existing
marker Forms with a 0.75 scale about their station origin. Recoloring changes
paint only. Fig05 adds a transparent geographic overlay to the unchanged PDF.
"""
from common import *
import io,shutil,copy
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from pypdf.generic import ContentStream,DecodedStreamObject,FloatObject

INPUTS={}
RGB=re.compile(rb'([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s+(RG|rg)\b')
def read(rel):
    p,h=source(rel);INPUTS[rel]={'sha256':h,'commit':BASE,'actual_bytes':Path(lp(p)).stat().st_size}
    return lp(p)
def native(key):return fitz.open(read('results/figure_review/'+key+'.pdf'))
def rgb(h):return tuple(to_rgb(h))
def recolor(doc,old,new):
    count=0;changed=[]
    for x in streams(doc):
        raw=doc.xref_stream(x)
        def sub(m):
            nonlocal count
            color=np.array([float(m.group(i)) for i in [1,2,3]])
            if np.max(np.abs(color-rgb(old)))<3e-5:
                count+=1;return (' '.join(f'{v:.8f}' for v in rgb(new))+' '+m.group(4).decode()).encode()
            return m.group(0)
        newraw=RGB.sub(sub,raw)
        if newraw!=raw:
            # All geometry/text/operators outside affected color numbers exact.
            assert RGB.sub(b'COLOR',newraw)==RGB.sub(b'COLOR',raw)
            doc.update_stream(x,newraw);changed.append(x)
    assert count>0
    return {'color_operators_changed':count,'changed_streams':changed,'old':old,'new':new,
        'noncolor_bytes_unchanged':True}

def framework():
    d=native('Main/Fig01');p=d[0];marker=[]
    for x in streams(d):
        raw=d.xref_stream(x)
        if len(raw)>1300 or not re.search(rb'\bm\b',raw) or not re.search(rb'\bB\b',raw):continue
        typ,box=d.xref_get_key(x,'BBox')
        if typ!='array':continue
        bounds=np.array([float(v) for v in re.findall(r'-?[0-9.]+',box)])
        if len(bounds)!=4 or max(abs(bounds))>9:continue
        # Origin is the exact station/point position; do not move Do calls.
        d.update_stream(x,b'q .75 0 0 .75 0 0 cm\n'+raw+b'\nQ')
        marker.append({'xref':x,'scale':.75,'origin':[0,0],'original_path_sha256':hashlib.sha256(raw).hexdigest()})
    assert len(marker)==12,marker
    # Inline scatter circles in source illustrations (no badge circles, text,
    # geographic polygons, line segments, or arrows). Preserve each center.
    inline=[]
    num=rb'[+-]?(?:\d+(?:\.\d*)?|\.\d+)'
    pair=num+rb'\s+'+num
    cubic=(num+rb'\s+')*6+rb'c\s*'
    circle_pattern=re.compile(pair+rb'\s+m\s*(?:'+cubic+rb'){8}h\s*(?:B\*?|f\*?)\b')
    for x in streams(d):
        raw=d.xref_stream(x)
        if len(raw)>4000000 or len(raw)<1300 or b' c' not in raw:continue
        edits=[]
        def shrink_circle(m):
            vals=[float(v) for v in re.findall(num,m.group(0))];pts=np.array(vals).reshape(-1,2)
            lo=pts.min(axis=0);hi=pts.max(axis=0);wh=hi-lo
            if 0<min(wh)<=max(wh)<7:
                c=(lo+hi)/2
                edits.append({'center':c.tolist(),'dimensions_before':wh.tolist(),'scale':.75,
                    'original_path_sha256':hashlib.sha256(m.group(0)).hexdigest()})
                # Preserve every original path byte, stroke and connected line.
                return f'q .75 0 0 .75 {c[0]*.25:.10f} {c[1]*.25:.10f} cm\n'.encode()+m.group(0)+b'\nQ'
            return m.group(0)
        updated=circle_pattern.sub(shrink_circle,raw)
        if edits:
            d.update_stream(x,updated);inline.append({'xref':x,'circles':edits,'all_nonmarker_bytes_unchanged':True})
    # Remove exactly the replaced Recovery labels, leaving other Stage5 text.
    edits=[];origins=[]
    for s in spans(p):
        if s['text'].replace('\xa0',' ').replace('\xad','-') in ['Service loss (0-480 h)','All + hospital tracts','T80: time to 80%']:
            edits.append(s['text']);origins.append((s['origin'][0],p.rect.height-s['origin'][1]))
    assert len(edits)==3,edits
    removed=0
    for x in streams(d):
        raw=d.xref_stream(x)
        def remove_text(m):
            nonlocal removed
            point=re.search(rb'1 0 0 1 ([0-9.]+) ([0-9.]+) Tm',m.group(0))
            if point and any(max(abs(float(point.group(1))-a),abs(float(point.group(2))-b))<.002 for a,b in origins):
                removed+=1;return b''
            return m.group(0)
        changed=re.sub(rb'\bBT\b.*?\bET\b',remove_text,raw,flags=re.S)
        if changed!=raw:d.update_stream(x,changed)
    assert removed==3,removed
    # White only the distribution illustration; existing headings and lists stay.
    p.draw_rect(fitz.Rect(125*MM,175*MM,154.6*MM,184.9*MM),color=None,fill=(1,1,1))
    text(p,139,176.6,'Schematic',7.5,center=True,color=rgb('#555555'))
    # Illustrative four bars, no numeric axis. This has no scientific values.
    # Nonmonotone contrasts avoid suggesting that vulnerability mechanically
    # increases loss. The schematic is not an additional policy estimate.
    x0=127.5;bottom=182.1;barheights=[4.6,3.3,3.8,2.0]
    for i,height in enumerate(barheights):
        x=x0+i*6.1
        p.draw_rect(fitz.Rect(x*MM,(bottom-height)*MM,(x+3.1)*MM,bottom*MM),color=None,
                    fill=rgb('#668ba0' if i<3 else '#b66d45'))
        text(p,x+1.55,184.5,f'Q{i+1}',7.5,center=True)
    # Bracket visibly relates Q1 and Q4 bar-top levels, without claiming values.
    xx=150.5;y1=bottom-barheights[0];y4=bottom-barheights[3]
    p.draw_line((xx*MM,y4*MM),(xx*MM,y1*MM),color=rgb('#444444'),width=.5)
    for yy in [y1,y4]:p.draw_line(((xx-.5)*MM,yy*MM),((xx+.5)*MM,yy*MM),color=rgb('#444444'),width=.5)
    text(p,151.6,179.8,'Gap',7.5,color=rgb('#444444'))
    for yy,label in [(188,'Cumulative service loss'),(191.5,'All tracts and'),(195,'hospital-linked tracts'),(198.5,'T80: time to 80%')]:
        text(p,110,yy,label,7.5,center=True)
    return d,{'marker_forms':marker,'inline_circle_edits':inline,'linear_marker_reduction_percent':25,
        'marker_origins_and_Do_invocations_preserved':True,'replacement_recovery_labels':edits,
        'distribution_illustration':'nonquantitative Q1-Q4 bars and separation bracket',
        'bar_heights_mm_for_drawing_only':barheights,'stage_positions_connections_preserved':True}

def t80():
    d=native('Main/Fig03');lut=plt.get_cmap('YlGnBu')(np.linspace(0,1,256))[:,:3]
    t=np.linspace(0,1,256);adjust=np.where(t<.25,.12+.52*t,t)
    proposed=plt.get_cmap('YlGnBu')(adjust)[:,:3]
    changes=0;unchanged_high=0
    for x in streams(d):
        raw=d.xref_stream(x)
        def sub(m):
            nonlocal changes,unchanged_high
            color=np.array([float(m.group(i)) for i in [1,2,3]])
            distances=np.max(np.abs(lut-color),axis=1);idx=int(np.argmin(distances))
            if distances[idx]<3e-5:
                if t[idx]>=.25:unchanged_high+=1;return m.group(0)
                changes+=1;return (' '.join(f'{v:.10f}' for v in proposed[idx])+' '+m.group(4).decode()).encode()
            return m.group(0)
        updated=RGB.sub(sub,raw)
        if updated!=raw:
            assert RGB.sub(b'COLOR',raw)==RGB.sub(b'COLOR',updated)
            d.update_stream(x,updated)
    # Existing indexed raster colorbar: recolor its LUT only; all scalar pixels,
    # range labels, positions, and geometry remain exact. Do not rasterize maps.
    imgs=d[0].get_images();assert len(imgs)==1
    x=imgs[0][0];kind,cs=d.xref_get_key(x,'ColorSpace');m=re.search(r'<([0-9A-Fa-f]+)>',cs);assert m
    lookup=bytearray.fromhex(m.group(1));n=0
    for i in range(0,len(lookup),3):
        color=np.array(lookup[i:i+3])/255
        idx=int(np.argmin(np.max(np.abs(lut-color),axis=1)))
        if t[idx]<.25:
            lookup[i:i+3]=np.round(proposed[idx]*255).astype(np.uint8).tobytes();n+=1
    d.xref_set_key(x,'ColorSpace','[/Indexed /DeviceRGB 255 <'+lookup.hex()+'>]')
    assert changes>0
    return d,{'authority_colormap':'YlGnBu, observed in actual current PDF',
        'proposal':'retain middle/high colors; low quarter t -> 0.12 + 0.52 t',
        'low_color_operators_changed':changes,'middle_high_color_operators_unchanged':unchanged_high,
        'colorbar_lookup_entries_changed':n,'normalization_range_and_missingness_changed':False,
        'map_paths_and_scalar_colorbar_pixels_unchanged':True}

def load_geography():
    rel='Data/LA_Tracts_With_Population'
    for suffix in ['.shp','.shx','.dbf','.prj']:read(rel+suffix)
    shapes=gpd.read_file(read(rel+'.shp'));shapes['tract_id']=shapes.GEOID.astype(str).str.zfill(11)
    meta=pd.read_csv(read('provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv'),dtype={'tract_id':str})
    assert meta.tract_id.str.fullmatch(r'\d{11}').all() and meta.tract_id.nunique()==2315
    assert meta.SOVI_quartile.isin(['Q1','Q2','Q3','Q4']).all()
    geo=shapes.merge(meta[['tract_id','SOVI_quartile']],on='tract_id',validate='one_to_one').to_crs(3310)
    assert len(geo)==2315
    # Degree spatial comparison provenance is checked using the saved mean
    # fields and all-tract summary means. None of these sources is written.
    v=pd.read_parquet(read('Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_TRACT_EFFECTS.parquet'))
    d=pd.read_parquet(read('Formal_Experiment_20260923/Formal_Results/TRACT_PAIRED_EFFECTS.parquet'))
    v=v[v.hazard.eq('2pc50')];d=d[d.hazard.eq('2pc50')&d.resource_scenario.eq('C57_D1')&d.strategy_id.eq('degree-first')&d.reference_strategy.eq('hospital-first')]
    values={}
    for ref in ['hospital-first','impact-first']:
        a=v[v.reference_strategy.eq(ref)];assert len(a)==2315 and a.valid_realizations.eq(1000).all()
        values[ref]=a.set_index('tract_id').mean_paired_delta_burden_hr.sort_index()
    assert len(d)==2315 and d.valid_paired_realizations.eq(1000).all()
    dd=d.set_index('tract_id').paired_mean_delta_burden_hr.sort_index()
    assert dd.index.equals(values['hospital-first'].index)
    values['degree-first']=values['hospital-first']-dd
    assert set(values['degree-first'].index)==set(geo.tract_id)
    formal=pd.read_parquet(read('Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet'))
    vf=pd.read_parquet(read('Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet'))
    def case(f,s):return f[f.hazard.eq('2pc50')&f.resource_scenario.eq('C57_D1')&f.strategy_id.eq(s)&f.mapping.eq('M1_UTILITY_003')&f.gate.eq('G1_BASELINE_050')]
    a=case(vf,'vulnerability-first');b=case(formal,'degree-first');assert len(a)==len(b)==1000
    expected=a.population_weighted_normalized_burden_hr.mean()-b.population_weighted_normalized_burden_hr.mean()
    pop=d.set_index('tract_id').population.reindex(dd.index)
    displayed=np.average(values['degree-first'],weights=pop);assert abs(expected-displayed)<1e-9
    audit={'quartile_authority':'frozen FEMA NRI v1.19 SOVI assignments used by formal Vulnerability-first',
        'domain_tracts':2315,'quartile_counts':{k:int(n) for k,n in geo.SOVI_quartile.value_counts().sort_index().items()},
        'quartile_GEOID_assignment_sha256':hashlib.sha256(meta[['tract_id','SOVI_quartile']].sort_values('tract_id').to_csv(index=False).encode()).hexdigest(),
        'degree_formula':'(Vulnerability - Hospital) - (Degree - Hospital)',
        'degree_population_weighted_change_hr':float(displayed),'degree_saved_summary_change_hr':float(expected),
        'common_effect_range_hr':[-max(abs(x).max() for x in values.values()),max(abs(x).max() for x in values.values())]}
    return geo,audit

def overlay_quartiles(geo,dissolve=False):
    plt.rcParams.update({'font.family':'Arial','pdf.fonttype':42,'font.size':8})
    fig=plt.figure(figsize=(185/25.4,74/25.4));fig.patch.set_alpha(0)
    bounds=geo.total_bounds
    q4=geo[geo.SOVI_quartile.eq('Q4')]
    for i in range(3):
        ax=fig.add_axes([.012+i*.330,.23,.316,.65]);ax.patch.set_alpha(0)
        outlines=gpd.GeoSeries([q4.geometry.union_all()],crs=geo.crs) if dissolve else q4.geometry
        outlines.boundary.plot(ax=ax,color='#303030',lw=.24,alpha=.75)
        ax.set_xlim(bounds[0],bounds[2]);ax.set_ylim(bounds[1],bounds[3]);ax.set_aspect('equal');ax.axis('off')
    label='Thin dark outlines: Q4 areas (highest social vulnerability)' if dissolve else 'Thin dark outlines: Q4 (highest social vulnerability)'
    fig.text(.5,.965,label,ha='center',va='top',fontsize=8)
    b=io.BytesIO();fig.savefig(b,format='pdf',transparent=True);plt.close(fig)
    overlay=fitz.open(stream=b.getvalue(),filetype='pdf');doc=native('Main/Fig05')
    doc[0].show_pdf_page(fitz.Rect(0,175*MM,185*MM,249*MM),overlay,0)
    return doc

def locator(geo):
    fig=plt.figure(figsize=(185/25.4,60/25.4))
    ax=fig.add_axes([.025,.04,.42,.86]);colors={'Q1':'#d2dce4','Q2':'#abbcc9','Q3':'#8096a8','Q4':'#445f73'}
    for q,c in colors.items():geo[geo.SOVI_quartile.eq(q)].plot(ax=ax,color=c,edgecolor='white',lw=.06)
    ax.set_xlim(geo.total_bounds[0],geo.total_bounds[2]);ax.set_ylim(geo.total_bounds[1],geo.total_bounds[3]);ax.set_aspect('equal');ax.axis('off')
    fig.text(.46,.91,'Social-vulnerability groups',fontsize=9,fontweight='bold')
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(facecolor=c,label=q+(' highest' if q=='Q4' else ' lowest' if q=='Q1' else '')) for q,c in colors.items()],
        loc='center left',bbox_to_anchor=(.46,.62),frameon=False,ncol=2,fontsize=8)
    fig.text(.46,.28,'Frozen FEMA NRI v1.19 SOVI quartiles\nQ4 dependency informs substation priorities;\ntracts are not repair tasks.',fontsize=8,linespacing=1.5)
    b=io.BytesIO();fig.savefig(b,format='pdf');plt.close(fig)
    inset=fitz.open(stream=b.getvalue(),filetype='pdf');old=native('Main/Fig05');doc=fitz.open()
    p=doc.new_page(width=185*MM,height=310*MM)
    p.show_pdf_page(fitz.Rect(0,0,185*MM,250*MM),old,0)
    p.show_pdf_page(fitz.Rect(0,250*MM,185*MM,310*MM),inset,0)
    return doc

def main():
    records={};d,info=framework();records['Fig01']=dict(export(d,'Fig01_Author_Review'),edits=info)
    d,info=t80();records['Fig03']=dict(export(d,'Fig03_Low_End_Palette'),edits=info)
    geo,qa=load_geography();dump('QUARTILE_AND_DEGREE_PROVENANCE.json',qa)
    d=overlay_quartiles(geo);records['Fig05_outline']=export(d,'alternatives/Fig05_Q4_Outline')
    # The locator prototype does not shrink any existing map or label.
    d=locator(geo);records['Fig05_locator']=export(d,'alternatives/Fig05_Quartile_Locator')
    for option,new in [('A','#648890'),('B','#7b828f')]:
        d=native('Main/Fig07');info=recolor(d,'#68a9b5',new)
        records['Fig07_'+option]=dict(export(d,'alternatives/Fig07_Color_'+option),edits=info,cluster_id=4)
    # Proposed recommendation is checked against actual renders before delivery.
    d=native('Supplement/FigS09');info=recolor(d,'#68a9b5','#7b828f')
    records['FigS09']=dict(export(d,'FigS09_Palette_Synchronization'),edits=info,cluster_id=4)
    dump('ARTWORK_EDIT_RECORDS.json',records);dump('SOURCE_HASHES.json',INPUTS)
    print(json.dumps({k:{a:v[a] for a in ['size_mm','min_font_pt']} for k,v in records.items()},indent=2))

if __name__=='__main__':main()
