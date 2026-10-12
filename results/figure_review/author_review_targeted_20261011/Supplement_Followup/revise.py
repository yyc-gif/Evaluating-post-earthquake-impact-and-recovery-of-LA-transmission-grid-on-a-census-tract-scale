"""Targeted display changes using frozen PDFs and saved display tables only."""
from pathlib import Path
import sys,re,json,hashlib,shutil
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import common as c
P=Path(__file__).resolve().parent
c.PKG=P
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,SymLogNorm
from matplotlib.lines import Line2D

plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,
 'axes.titlesize':9,'axes.titleweight':'bold','xtick.labelsize':8,'ytick.labelsize':8,
 'legend.fontsize':8,'axes.linewidth':.6,'pdf.fonttype':42,'figure.facecolor':'white'})
SOURCES={};RECORDS={}
COLORS={'impact-first':'#ff7f00','hospital-first':'#555555','degree-first':'#4daf4a',
 'vulnerability-first':'#a65628','betweenness-first':'#b59a00','random':'#9a9a9a','unconstrained':'#000000'}
LABEL={k:k.replace('-',' ').title().replace(' First','-first') for k in COLORS}
LABEL['unconstrained']='Unconstrained';LABEL['random']='Random'
FOCAL=['impact-first','hospital-first','degree-first','vulnerability-first','unconstrained']
OTHER=['betweenness-first','random','unconstrained']
SELECTED=FOCAL[:4]+OTHER[:2]

def src(rel):
    p,h=c.source(rel);SOURCES[rel]={'sha256':h,'commit':c.BASE,'actual_bytes':p.stat().st_size};return p

def baseline(name):
    src('results/figure_review/Supplement/'+name+'.pdf')
    return c.fitz.open(c.lp(P/'before'/(name+'.pdf')))

def save(d,name,record):
    RECORDS[name]=c.export(d,name+'_Candidate')|record;d.close()

def replace_span(page,old,new,size=None,rotate=0):
    found=[s for s in c.spans(page) if s['text']==old];assert len(found)==1,(old,len(found))
    s=found[0];r=c.fitz.Rect(s['bbox']);sz=size or s['size']
    page.add_redact_annot(r,fill=(1,1,1));page.apply_redactions(images=0,graphics=0,text=0)
    fontfile='C:/Windows/Fonts/arialbd.ttf' if 'Bold' in s['font'] else 'C:/Windows/Fonts/arial.ttf'
    name='FollowupBold' if 'Bold' in s['font'] else 'FollowupArial'
    page.insert_font(fontname=name,fontfile=fontfile);f=c.fitz.Font(fontfile=fontfile)
    if rotate:origin=(s['origin'][0],(r.y0+r.y1+f.text_length(new,fontsize=sz))/2)
    else:origin=((r.x0+r.x1-f.text_length(new,fontsize=sz))/2,s['origin'][1])
    page.insert_text(origin,new,fontname=name,fontsize=sz,rotate=rotate)

def s03():
    d=baseline('FigS03');p=d[0];changed=[]
    for x in sorted({x for x,n,i,b in p.get_xobjects()}):
        raw=d.xref_stream(x)
        b=d.xref_get_key(x,'BBox')[1];nums=[float(v) for v in re.findall(r'-?\d+\.?\d*',b)]
        if raw and len(raw)<1400 and raw.count(b' c')>=4 and len(nums)==4 and max(abs(v) for v in nums)<6 and b' Do' not in raw:
            d.xref_set_key(x,'Resources','<< /ExtGState << /FollowupAlpha << /Type /ExtGState /CA .62 /ca .62 >> >> >>')
            d.update_stream(x,b'q\n/FollowupAlpha gs\n'+raw+b'\nQ\n');changed.append(x)
    assert changed
    travel=pd.read_csv(c.lp(src('data/travel/travel_task_to_task.csv')),index_col=0)
    assert travel.shape==(92,92)
    height=p.rect.height/c.MM-110
    fig=plt.figure(figsize=(185/25.4,height/25.4));ax=fig.add_axes([.15,.16,.67,.75])
    im=ax.pcolormesh(np.arange(93),np.arange(93),travel.to_numpy(),cmap='YlGnBu',vmin=0,
       vmax=float(travel.to_numpy().max()),shading='flat',rasterized=False)
    ax.set_ylim(92,0);ax.set_xticks([]);ax.set_yticks([])
    ax.set_xlabel('Destination substation',fontsize=8.5);ax.set_ylabel('Origin substation',fontsize=8.5)
    ax.set_title('B. Directed task-to-task travel',fontsize=9.5,pad=7)
    cb=fig.colorbar(im,cax=fig.add_axes([.855,.16,.025,.75]));cb.set_label('Travel time (h)',fontsize=8.5)
    cb.ax.tick_params(labelsize=7.5)
    f=P/'qa/S03_matrix.pdf';fig.savefig(c.lp(f));plt.close(fig)
    result=c.fitz.open();page=result.new_page(width=p.rect.width,height=p.rect.height)
    page.show_pdf_page(c.fitz.Rect(0,0,185*c.MM,110*c.MM),d,0,clip=c.fitz.Rect(0,0,185*c.MM,110*c.MM))
    with c.fitz.open(c.lp(f)) as matrix:page.show_pdf_page(c.fitz.Rect(0,110*c.MM,185*c.MM,p.rect.height),matrix,0)
    d.close()
    save(result,'FigS03',{'marker_form_xrefs':changed,'marker_opacity':.62,'six_digit_labels_removed':10,
       'marker_size_and_positions_unchanged':True,'directed_travel_values_and_palette_unchanged':True,
       'full_directed_matrix_display_preserved':True,'max_directional_difference_h':float(abs(travel.values-travel.values.T).max())})

def s06():
    d=baseline('FigS06');p=d[0]
    replace_span(p,'B. Threshold and source requirement removed','B. Combined threshold and source removal')
    c.text(p,92.5,65,'B removes both requirements; C and D retain source connectivity.',8,center=True,font_prefix='Followup')
    config=json.load(open(c.lp(src('config/parent_frozen_design/FINAL_EXPERIMENT_MATRIX.json')),encoding='utf-8'))
    gates=config['offline_robustness']['2pc50_C57_gate_cases']
    record=json.load(open(c.lp(src('docs/reproducibility/SUPPLEMENT_ASSUMPTIONS_LAYOUT_UPDATE_20261006.json')),encoding='utf-8'))
    record=next(r for r in record if r.get('file')=='Supplement/FigS06.pdf')
    actual={}
    for r in record['source_tables']:
        # The per-policy offline shards are local frozen files registered by
        # the committed display record, rather than individually tracked blobs.
        f=c.ORIGINAL/r['path'];assert c.sha(f)==r['sha256']
        SOURCES[r['path']]={'sha256':r['sha256'],'registered_by_commit':c.BASE,
           'actual_local_path':str(f),'actual_bytes':f.stat().st_size,'individually_git_tracked':False}
        t=pd.read_parquet(c.lp(f));actual[r['path']]=sorted(t.gate.unique().tolist())
    assert set(gates)=={'G0_NO_GATE','G1_BASELINE_050','G2_RELAXED_005','G3_STRICT_075'}
    c.dump('S06_GATE_DESIGN_AUDIT.json',{'registered_gates':gates,'actual_saved_gates':actual,
       'production':'e = f * F_0.50 * C_14Core','combined_removal':'e = f',
       'isolated_threshold_removal_available':False,'isolated_source_removal_available':False,
       'new_gate_evaluation_performed':False,'displayed_statistics':record['displayed_summary']})
    save(d,'FigS06',{'display_statistics_unchanged':True,'B_is_combined_removal':True,'new_controls_fabricated':False})

def s07():
    old=baseline('FigS07');summary=pd.read_csv(c.lp(src('results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv')))
    assert not summary.duplicated(['strategy','time_hr']).any()
    data=summary[summary.strategy.isin(SELECTED+['unconstrained'])].copy()
    assert data.groupby('strategy').size().to_dict()=={k:9 for k in SELECTED+['unconstrained']}
    np.testing.assert_allclose(data.population_dependency_weighted_R_conn,
      data.population_dependency_weighted_fixed_precomputed_best_path_connection+
      data.population_dependency_weighted_full_minus_fixed_precomputed_best_path,atol=1e-12)
    fields=['population_dependency_weighted_R_conn','population_dependency_weighted_fixed_precomputed_best_path_connection',
       'population_dependency_weighted_full_minus_fixed_precomputed_best_path']
    H=142;fig=plt.figure(figsize=(185/25.4,H/25.4));fig.text(.5,1-3/H,
        'A. Source connection: full network and fixed path',ha='center',va='top',fontsize=9.5,fontweight='bold')
    quantity=[Line2D([],[],color='#333333',lw=1.1,label='Full network'),Line2D([],[],color='#333333',lw=1.1,ls='--',label='Fixed precomputed path')]
    fig.legend(handles=quantity,loc='upper center',bbox_to_anchor=(.5,1-8/H),ncol=2,frameon=False,
       handlelength=2.1,handletextpad=.5,columnspacing=2)
    identities=[];display_rows=[]
    for col,(x,keys,title) in enumerate([(.115,FOCAL,'Four focal policies + Unconstrained'),(.615,OTHER,'Other selected policies + Unconstrained')]):
        ax=fig.add_axes([x,1-60/H,.345,36/H]);ax.set_title(title,fontsize=8,pad=5)
        for k in keys:
            q=data[data.strategy.eq(k)].sort_values('time_hr')
            for field,ls in [(fields[0],'-'),(fields[1],'--')]:
                ax.plot(q.time_hr,q[field],color=COLORS[k],ls=ls,lw=1.1)
                display_rows.extend({'panel':'A','view':col,'strategy':k,'time_hr':float(t),'field':field,'value':float(v)} for t,v in zip(q.time_hr,q[field]))
        ax.set(xlim=(0,120),ylim=(-.02,1.04),xticks=[0,24,48,72,96,120]);ax.set_ylabel('Probability of being functional\nand source-connected' if col==0 else '')
        ax.spines[['top','right']].set_visible(False);ax.grid(color='#e5e5e5',lw=.4)
        handles=[Line2D([],[],color=COLORS[k],lw=1.1,label=LABEL[k]) for k in keys]
        fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(x+.1725,1-66/H),ncol=2,
           frameon=False,handlelength=1.5,handletextpad=.45,columnspacing=.9,labelspacing=.25)
        identities.append({'view':col,'policy_curves':keys,'policy_legend':keys,'applies_to':['A','B'],'markers_in_legend':False})
        ax=fig.add_axes([x,1-124/H,.345,29/H])
        for k in keys:
            q=data[data.strategy.eq(k)].sort_values('time_hr');ax.plot(q.time_hr,q[fields[2]],color=COLORS[k],lw=1.1)
            display_rows.extend({'panel':'B','view':col,'strategy':k,'time_hr':float(t),'field':fields[2],'value':float(v)} for t,v in zip(q.time_hr,q[fields[2]]))
        ax.set(xlim=(0,120),ylim=(-.005,.235),xticks=[0,24,48,72,96,120],xlabel='Time after earthquake (h)')
        ax.set_ylabel('Increase in source-\nconnection probability' if col==0 else '')
        ax.spines[['top','right']].set_visible(False);ax.grid(color='#e5e5e5',lw=.4)
    fig.text(.5,1-88/H,'B. Additional source connection from alternate routes',ha='center',va='top',fontsize=9.5,fontweight='bold')
    c.dump('S07_DISPLAYED_VALUES.json',{'source_sha256':SOURCES['results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv']['sha256'],
       'legend_identities':identities,'displayed_rows':display_rows,'unconstrained_repeated_as_same_reference':True})
    f=P/'qa/S07_dynamic_panels.pdf';fig.savefig(c.lp(f));plt.close(fig)
    # Preserve native maps and numeric scales. Only their conditional wording changes.
    replace_span(old[0],'C. Conditional source reachability','C. Source access from a functional station',size=9)
    replace_span(old[0],'Conditional source-path reliability','Probability, given a functional station',size=8)
    result=c.fitz.open();p=result.new_page(width=185*c.MM,height=(H+85)*c.MM)
    with c.fitz.open(c.lp(f)) as dynamic:p.show_pdf_page(c.fitz.Rect(0,0,185*c.MM,H*c.MM),dynamic,0)
    p.show_pdf_page(c.fitz.Rect(0,H*c.MM,185*c.MM,(H+85)*c.MM),old,0,clip=c.fitz.Rect(0,135*c.MM,185*c.MM,220*c.MM))
    old.close();save(result,'FigS07',{'policy_keys':identities,'all_saved_curve_values_used_exactly':True,
       'static_map_geometry_and_color_scales_preserved':True,'static_panels_vertical_translation_mm':7})

NUMBER=rb'[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)'
RGB=re.compile(rb'('+NUMBER+rb')\s+('+NUMBER+rb')\s+('+NUMBER+rb')\s+(rg|RG)\b')

def s10():
    d=baseline('FigS10')
    source=LinearSegmentedColormap.from_list('population_context',plt.get_cmap('Blues')(np.linspace(.1,.65,256)))
    destination=LinearSegmentedColormap.from_list('neutral_population',['#f3f3f3','#c6c6c6','#8d8d8d'])
    old=source(np.linspace(0,1,256))[:,:3];new=destination(np.linspace(0,1,256))[:,:3];counts=[]
    for x in c.streams(d):
        raw=d.xref_stream(x);count=[0]
        def recolor(m):
            rgb=np.array([float(m[i]) for i in [1,2,3]]);dist=np.max(abs(old-rgb),axis=1);i=int(dist.argmin())
            if dist[i]<2e-6:
                count[0]+=1;return ('%.9f %.9f %.9f '%tuple(new[i])).encode()+m[4]
            return m[0]
        updated=RGB.sub(recolor,raw)
        if count[0]:d.update_stream(x,updated);counts.append({'xref':x,'color_operators':count[0]})
    assert sum(r['color_operators'] for r in counts)>1000
    images=[]
    for x in range(1,d.xref_length()):
        if d.xref_get_key(x,'Subtype')[1]!='/Image':continue
        cs=d.xref_get_key(x,'ColorSpace')[1];match=re.search(r'<([0-9A-Fa-f]+)>',cs)
        if not match:continue
        arr=np.frombuffer(bytes.fromhex(match[1]),dtype=np.uint8).reshape(-1,3)/255
        mapped=[]
        for rgb in arr:
            dist=np.max(abs(old-rgb),axis=1);i=int(dist.argmin());assert dist[i]<.01
            mapped.append(np.rint(new[i]*255).astype(np.uint8))
        cs=cs[:match.start(1)]+np.array(mapped,dtype=np.uint8).tobytes().hex()+cs[match.end(1):]
        original_indices=hashlib.sha256(d.xref_stream(x)).hexdigest();d.xref_set_key(x,'ColorSpace',cs)
        images.append({'xref':x,'scalar_index_stream_sha256':original_indices,'scalar_indices_unchanged':True})
    assert images
    save(d,'FigS10',{'C_population_palette':'neutral gray #f3f3f3 -> #c6c6c6 -> #8d8d8d',
       'color_operators_changed':counts,'colorbar_lookup_changes':images,'log_normalization_unchanged':True,
       'all_geographic_paths_priorities_and_text_unchanged':True})

def s11():
    baseline('FigS11').close()
    d=pd.read_csv(c.lp(src('provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv')))
    hazards=['LongBeach','SanFernando','Northridge','2pc50'];names=['Long Beach','San Fernando','Northridge','2pc50']
    fields=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr','population_T80_hr']
    values=[]
    for h in hazards:
        a=np.array([[d.loc[d.hazard.eq(h)&d.strategy_id.eq(k)&d.metric.eq(m),'mean_paired_difference'].item() for m in fields] for k in SELECTED]);values.append(a)
    limit=float(max(abs(a).max() for a in values));norm=SymLogNorm(linthresh=.10,linscale=1,vmin=-limit,vmax=limit,base=10)
    fig=plt.figure(figsize=(185/25.4,188/25.4));cmap=plt.get_cmap('RdBu_r')
    labels=['All-tract\nservice\nloss','Q4 tract\nservice\nloss','Hospital\ntract service\nloss','Population\nT80']
    for i,(h,name,a) in enumerate(zip(hazards,names,values)):
        ax=fig.add_axes([.19+(i%2)*.46,.195+(1-i//2)*.405,.30,.285])
        im=ax.pcolormesh(np.arange(5)-.5,np.arange(7)-.5,a,cmap=cmap,norm=norm,rasterized=False)
        ax.set_ylim(5.5,-.5);ax.set_xticks(range(4),labels,fontsize=7.5);ax.set_yticks(range(6),[LABEL[k] for k in SELECTED],fontsize=8)
        ax.tick_params(length=0,pad=4);ax.set_title(f'{chr(65+i)}. {name}',pad=6)
        ax.axvline(2.5,color='white',lw=1.2)
        for row in range(6):
            for col in range(4):
                rgb=cmap(norm(a[row,col]))[:3];lum=np.dot(rgb,[.2126,.7152,.0722])
                ax.text(col,row,f'{a[row,col]:+.2f}',ha='center',va='center',fontsize=7.5,color='white' if lum<.45 else '#15232a')
    cb=fig.colorbar(im,cax=fig.add_axes([.18,.085,.76,.014]),orientation='horizontal',ticks=[-9,-5,-1,-.1,0,.1,1,5,9])
    cb.ax.set_xticklabels(['-9','-5','-1','-0.1','0','0.1','1','5','9']);cb.set_label('Mean change relative to Unconstrained (h)',fontsize=8.5,labelpad=4)
    cb.ax.tick_params(labelsize=8,length=2);cb.ax.minorticks_off()
    fig.text(.5,.025,'Shared signed-log colors: linear within +/-0.10 h; printed values are hours.',ha='center',fontsize=8)
    f=P/'qa/S11_panels.pdf';fig.savefig(c.lp(f));plt.close(fig)
    c.dump('S11_DISPLAYED_VALUES.json',{'policy_order':SELECTED,'hazards':hazards,'fields':fields,'values':[a.tolist() for a in values],
       'same_hour_limits':[-limit,limit],'color_normalization':'SymLogNorm','linthresh_h':.1,'base':10,
       'metric_or_hazard_specific_rescaling':False,'outliers_clipped':False,'cell_annotations_unchanged':True})
    save(c.fitz.open(c.lp(f)),'FigS11',{'mean_values_and_annotations_unchanged':True,'same_hour_limits':[-limit,limit],
       'shared_nonlinear_color_scale':True,'linthresh_h':.1,'outliers_clipped':False,'all_four_hazards_preserved':True})

if __name__=='__main__':
    for fn in [s03,s06,s07,s10,s11]:print('Rendering',fn.__name__,flush=True);fn()
    for rel in ['src/la_grid/revision/r1_source_gate.py','src/la_grid/revision/r1_mapping_gate_robustness.py',
      'src/la_grid/diagnostics/source_terminal_operational_reliability.py','src/la_grid/plotting/selected_strategy_source_travel.py',
      'src/la_grid/plotting/clarify_distribution_strategy_visibility.py','src/la_grid/plotting/selected_strategy_panels.py',
      'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md']:src(rel)
    c.dump('SOURCE_HASHES.json',SOURCES);c.dump('ARTWORK_EDIT_RECORDS.json',RECORDS)
    print('Completed five review-only candidates.',flush=True)
