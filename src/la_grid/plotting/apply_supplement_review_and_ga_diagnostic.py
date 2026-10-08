"""Bounded supplement display fixes and GA-budget diagnostic presentation.

Reads stored artwork, GIS and fixed policy orders. Does not alter any model,
formal objective, planning sample, evaluation trajectory or scientific table.
"""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, tempfile
import fitz
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from la_grid.paths import REPO_ROOT
from la_grid.plotting import build_meeting_figure_collection as meeting
from la_grid.plotting.apply_outcome_display_feedback import fonts, update_csv, sha
from la_grid.plotting.apply_map_metric_identity_feedback import CLUSTER_COLORS, export, packets
from la_grid.plotting.refine_policy_cluster_presentation import streams

ROOT=REPO_ROOT
REVIEW=ROOT/'results/figure_review'
HISTORY=ROOT/'provenance/figure_review_history/supplement_display_before_20261008'
TEMP=Path(tempfile.gettempdir())/'la_supplement_display_20261008'
MM=72/25.4
plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],'font.size':7.5,
 'axes.titlesize':9.5,'axes.titleweight':'bold','axes.labelsize':8.5,
 'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,
 'axes.linewidth':.6,'pdf.fonttype':42,'figure.facecolor':'white'})

def original(key):
 p=REVIEW/(key+'.pdf');old=HISTORY/(key+'.pdf');old.parent.mkdir(parents=True,exist_ok=True)
 for ext in ['.pdf','.png']:
  if not old.with_suffix(ext).exists():shutil.copy2(p.with_suffix(ext),old.with_suffix(ext))
 return old

def s01():
 key='Supplement/FigS01';old=original(key)
 hazards=['LongBeach','SanFernando','Northridge','2pc50']
 labels=['Long Beach','San Fernando','Northridge','2pc50']
 colors=['#366e9f','#00856a','#9a7559','#a65628']
 suite=ROOT/'results/revised_suite/LA_Grid_Revised_Suite_20260925/Stage 1 Output_expanded'
 fig,ax=plt.subplots(figsize=(185/25.4,66/25.4));fig.subplots_adjust(left=.125,right=.985,bottom=.23,top=.88)
 values=[];sources=[]
 for h in hazards:
  p=suite/f'MC_Device_Damage_AvgDS_{h}.csv';v=pd.read_csv(p).avg_damage_state.to_numpy();assert len(v)==92
  values.append(v);sources.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'station_count':len(v)})
 boxes=ax.boxplot(values,positions=range(4),widths=.42,patch_artist=True,showfliers=False,
  medianprops={'color':'#303030','linewidth':.8},whiskerprops={'linewidth':.6},capprops={'linewidth':.6})
 for i,(v,color,box) in enumerate(zip(values,colors,boxes['boxes'])):
  box.set_facecolor(color);box.set_alpha(.2);box.set_edgecolor(color);box.set_linewidth(.7)
  ax.scatter(np.full(len(v),i),v,s=8,c=color,edgecolors='white',linewidths=.2,zorder=4,alpha=.75)
 ax.set_ylim(-.05,4.15);ax.set_xticks(range(4),labels);ax.set_ylabel('Mean substation damage state')
 ax.set_title('A. Substation damage severity',pad=5);ax.spines[['top','right']].set_visible(False)
 ax.grid(axis='y',color='#e5e5e5',lw=.4,zorder=0)
 p=TEMP/'s01_vertical_station_values.pdf';fig.savefig(p);plt.close(fig)
 doc=fitz.open(old);page=doc[0];rect=fitz.Rect(0,0,185*MM,66*MM)
 page.add_redact_annot(rect,fill=(1,1,1));page.apply_redactions(images=2,graphics=2,text=0)
 with fitz.open(p) as d:page.show_pdf_page(rect,d,0)
 return export(doc,key,{'change':'Station points align vertically at each hazard; no horizontal jitter. Existing B maps retained.', 'sources':sources})

def s04():
 key='Supplement/FigS04';doc=fitz.open(original(key));count=0
 pattern=re.compile(rb'\[[^\]]*\]\s*[-+0-9.]+\s+d\b')
 for x in streams(doc):
  raw=doc.xref_stream(x)
  # Color and emphasis distinguish policies; no arbitrary solid/dashed priority.
  new,n=pattern.subn(b'[] 0 d',raw);count+=n
  if new!=raw:doc.update_stream(x,new)
 return export(doc,key,{'change':'All policy and corresponding legend strokes are solid; curve vertices unchanged.', 'dash_operator_count':count})

def s09():
 key='Supplement/FigS09';doc=fitz.open(original(key));p=doc[0]
 p.add_redact_annot(fitz.Rect(29*MM,0,91*MM,8*MM),fill=(1,1,1));p.apply_redactions(images=0,graphics=2,text=0)
 fonts(p)
 # Bottom-right inside A is outside the visible score cloud; belongs only to A.
 box=fitz.Rect(77*MM,51*MM,88.5*MM,73*MM);p.draw_rect(box,color=None,fill=(1,1,1),fill_opacity=.94)
 for i,(cluster,color) in enumerate(CLUSTER_COLORS.items()):
  y=(54+i*4)*MM;rgb=tuple(int(color[j:j+2],16)/255 for j in [1,3,5])
  p.draw_circle((79*MM,y-.6*MM),.7*MM,color=None,fill=rgb)
  p.insert_text((81*MM,y),f'C{cluster}',fontname='DisplayArial',fontsize=7.5)
 return export(doc,key,{'change':'Cluster legend moved inside Panel A; explicit cluster ID palette retained.'})

def s10():
 key='Supplement/FigS10';original(key)
 tracts=meeting.tract_geometry()
 nodes=pd.read_csv(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv',dtype={'id':str})
 names=pd.read_csv(ROOT/'Data/Substations_PGA_IDW_CEC_expanded.csv',dtype={'id':str})[['id','NAME']]
 points=meeting.map_points(nodes,tracts.crs).merge(names,on='id',validate='one_to_one')
 mapping=pd.read_csv(ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str,'substation_id':str})
 hosp=pd.read_csv(ROOT/'Data/hospital_with_tract_expanded.csv',dtype={'GEOID':str})
 hospids=set(hosp.GEOID.str.replace(r'\.0$','',regex=True).str.zfill(11))
 mapping['tract_norm']=mapping.tract_id.str.replace(r'\.0$','',regex=True).str.zfill(11)
 eligible=set(mapping.loc[mapping.tract_norm.isin(hospids),'substation_id'])
 meta=pd.read_csv(ROOT/'provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv',dtype={'tract_id':str})
 q4=set(meta.loc[meta.SOVI_quartile.eq('Q4'),'tract_id'])
 formal=ROOT/'Formal_Experiment_20260923'
 rules=json.loads((formal/'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']
 vuln=json.loads((formal/'Equity_Amendment/VULNERABILITY_FIRST_SEQUENCE.json').read_text())
 assert len(q4)==vuln['Q4_tract_count']==579
 specs=[('hospital-first',rules['hospital-first'],hospids,'A. Hospital-first','#007c83'),
  ('vulnerability-first',vuln['ordered_station_ids'],q4,'B. Vulnerability-first','#8c6d31'),
  ('impact-first',rules['impact-first'],set(),'C. Impact-first','#e19243')]
 fig=plt.figure(figsize=(185/25.4,264/25.4));records=[]
 for i,(policy,sequence,highlight,title,color) in enumerate(specs):
  top=list(map(str,sequence[:5]));assert len(sequence)==92 and len(set(sequence))==92
  ax=fig.add_axes([.045,1-(i*86+79)/264,.91,70/264])
  meeting.draw_tract_base(ax,tracts,np.where(tracts.tract_id_norm.isin(highlight),'#e0d6e9','#f8f8f8'))
  ax.scatter(points.geometry.x,points.geometry.y,s=8,color='#71818d',edgecolors='white',lw=.25,zorder=3)
  if i==0:
   sel=points[points.id.isin(eligible)];ax.scatter(sel.geometry.x,sel.geometry.y,s=11,color='#a65628',edgecolors='white',lw=.25,zorder=4)
  selected=points[points.id.isin(top)];assert len(selected)==5
  ax.scatter(selected.geometry.x,selected.geometry.y,s=24,color=color,edgecolors='white',lw=.5,zorder=5)
  positions=[(.025,.89,'left'),(.975,.88,'right'),(.025,.43,'left'),(.975,.48,'right'),(.975,.17,'right')]
  for station,pos in zip(top,positions):
   row=points[points.id.eq(station)].iloc[0]
   ax.annotate(row.NAME,(row.geometry.x,row.geometry.y),xytext=pos[:2],textcoords='axes fraction',ha=pos[2],va='center',
    fontsize=7.5,color='#26343d',fontweight='bold',arrowprops={'arrowstyle':'-','color':'#687980','lw':.5},
    bbox={'facecolor':'white','edgecolor':'none','alpha':.9,'pad':.6},zorder=6)
   records.append({'policy':policy,'station':station,'name':row.NAME})
  ax.set_title(title,pad=5)
  handles=[Line2D([],[],marker='o',ls='none',color='#71818d',ms=3.5,label='Substations'),
   Line2D([],[],marker='o',ls='none',color=color,ms=4.5,label='First five repair priorities')]
  if i<2:handles.insert(0,Patch(facecolor='#e0d6e9',label='Hospital-linked tracts' if i==0 else 'Highest-vulnerability quartile'))
  if i==0:handles.append(Line2D([],[],marker='o',ls='none',color='#a65628',ms=3.5,label='Hospital-priority substations'))
  ax.legend(handles=handles,ncol=2 if i==0 else 3,loc='upper center',bbox_to_anchor=(.5,-.012),frameon=False,
   columnspacing=1.1,handletextpad=.4,borderaxespad=0)
 out=TEMP/'s10_parallel_priority_maps.pdf';fig.savefig(out);plt.close(fig)
 return export(fitz.open(out),key,{'change':'Three equal-size priority maps, same geographic extent and station-label font. Fixed orders unchanged.', 'top_five_stations':records})

def integrate(records):
 changed={r['file']:r for r in records};generator=Path(__file__).relative_to(ROOT).as_posix()
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 def idx(row):
  p=ROOT/row['source_path'];key=p.relative_to(REVIEW).with_suffix('.pdf').as_posix()
  if key in changed:
   shutil.copy2(p,ROOT/'results/figures'/row['file'])
   row.update(sha256_or_lfs_oid='sha256:'+sha(p),generator=generator,notes='Current author-requested supplement presentation and independent GA-budget diagnostic.')
 update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',idx)
 def manifest(row):
  key=Path(row['final_name']).with_suffix('.pdf').as_posix()
  if key in changed:
   p=REVIEW/row['final_name'];old=HISTORY/row['final_name']
   row.update(source_commit='SUPPLEMENT_DISPLAY_UPDATE_20261008',sha256=sha(p),parent_source_commit=head,
    parent_source_file=old.relative_to(ROOT).as_posix(),parent_sha256=sha(old),min_font_pt=f"{changed[key]['min_font_pt']:.3f}",status='AUTHOR_REQUESTED_CURRENT_DISPLAY')
 update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
 p=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';a=json.loads(p.read_text())
 a['current_code_files']=[x for x in a['current_code_files'] if x['path']!=generator]+[{'path':generator,'sha256':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'tracked_in_current_git':True}]
 p.write_text(json.dumps(a,indent=2)+'\n')
 audit_path=ROOT/'docs/reproducibility/SUPPLEMENT_DISPLAY_FEEDBACK_20261008.json'
 previous=json.loads(audit_path.read_text()) if audit_path.exists() else []
 combined={r['file']:r for r in previous};combined.update({r['file']:r for r in records})
 audit_path.write_text(json.dumps(list(combined.values()),indent=2)+'\n')

if __name__=='__main__':
 TEMP.mkdir(exist_ok=True);records=[s01(),s04(),s09(),s10()];integrate(records)
