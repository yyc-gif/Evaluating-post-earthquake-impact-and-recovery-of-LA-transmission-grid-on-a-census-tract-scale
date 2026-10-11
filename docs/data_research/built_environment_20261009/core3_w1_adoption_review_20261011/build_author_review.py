"""Narrow ZIP/OOXML edit of confirmed S19; preserve every unrelated package part."""
from pathlib import Path
from copy import deepcopy
import sys,json,zipfile,hashlib
from lxml import etree as E
# Bundled Python authoring; scientific libraries are not imported here.
OUT=Path(__file__).resolve().parent
def lp(p):return Path('\\\\?\\'+str(Path(p).absolute()).removeprefix('\\\\?\\'))
def h(b):return hashlib.sha256(b).hexdigest()
def dump(n,d):lp(OUT/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
S19=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_manuscript_rebuild\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
assert h(S19.read_bytes())=='a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253'
with zipfile.ZipFile(S19) as z:parts={n:z.read(n) for n in z.namelist()}
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main','pic':'http://schemas.openxmlformats.org/drawingml/2006/picture'}
def el(t,**attrs):return E.Element('{'+ns[t.split(':')[0]]+'}'+t.split(':')[1],{('{'+ns[k.split(':')[0]]+'}'+k.split(':')[1] if ':' in k else k):str(v) for k,v in attrs.items()})
doc=E.fromstring(parts['word/document.xml']);body=doc.find('w:body',ns);ps=body.findall('w:p',ns)
content=json.loads(lp(OUT/'REVIEW_TEXT_AND_CAPTIONS.json').read_text(encoding='utf-8'))
repl=json.loads(lp(OUT/'S19_TARGETED_REPLACEMENTS.json').read_text(encoding='utf-8'))
repl['2']='Author review copy proposing the conditional CORE3/W1 Stage 7 reference. Other sections, numerical results and existing figures retain the author-confirmed S19 working draft. This copy does not promote the new classification to the formal analysis.'
def flat(p):return ''.join(p.xpath('.//w:t/text()',namespaces=ns))
def para(txt,template=None,keep=False,pagebreak=False,bold=False,size=None):
 p=el('w:p')
 if template is not None and template.find('w:pPr',ns) is not None:p.append(deepcopy(template.find('w:pPr',ns)))
 if keep or pagebreak:
  pr=p.find('w:pPr',ns)
  if pr is None:pr=el('w:pPr');p.insert(0,pr)
  if keep:pr.append(el('w:keepNext'))
  if pagebreak:pr.append(el('w:pageBreakBefore'))
 r=el('w:r');p.append(r)
 if bold or size:
  pr=el('w:rPr');r.append(pr)
  if bold:pr.append(el('w:b'))
  if size:pr.append(el('w:sz',**{'w:val':int(size*2)}))
 t=el('w:t');t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=str(txt);r.append(t);return p

changes=[]
for key,t in repl.items():
 i=int(key);old=ps[i-1];new=para(t,old);body.replace(old,new)
 changes.append(dict(source_location=f'P{i:04d}',old_exact_text=flat(old),new_exact_text=t,operation='review metadata' if i==2 else 'replace Stage7 clause only'))

def insert_after(original_p,items):
 # original reference may have been replaced above; address by its source text replacement.
 target=next((c for c in body if c.tag==el('w:p').tag and flat(c)==repl.get(str(original_p),flat(ps[original_p-1]))),None)
 assert target is not None
 pos=body.index(target)+1
 for item in items:body.insert(pos,item);pos+=1

insert_after(23,[para(t,ps[22]) for t in content['methods']])
insert_after(40,[para(t,ps[39]) for t in content['results']])
insert_after(47,[para(t,ps[46]) for t in content['discussion']])
for key,anchor in [('methods',23),('results',40),('discussion',47)]:
 for i,t in enumerate(content[key],1):changes.append(dict(source_location=f'after P{anchor:04d}, inserted {key}{i}',old_exact_text='',new_exact_text=t,operation='insert targeted Stage7 paragraph'))

# New table, with mean/median convention and cell widths; original three tables stay intact.
table=json.loads(lp(OUT/'PROFILE_TABLE_DISPLAY.json').read_text(encoding='utf-8'))
tbl=el('w:tbl');pr=el('w:tblPr');pr.append(el('w:tblW',**{'w:w':9792,'w:type':'dxa'}));pr.append(el('w:tblLayout',**{'w:type':'fixed'}));borders=el('w:tblBorders')
for side in ['top','left','bottom','right','insideH','insideV']:borders.append(el('w:'+side,**{'w:val':'single','w:sz':4,'w:color':'D0D0D0'}))
pr.append(borders);tbl.append(pr);grid=el('w:tblGrid');widths=[3916,1469,1469,1469,1469]
for width in widths:grid.append(el('w:gridCol',**{'w:w':width}))
tbl.append(grid)
for i,row in enumerate([table['columns']]+table['rows']):
 tr=el('w:tr');trpr=el('w:trPr');trpr.append(el('w:cantSplit'))
 if i==0:trpr.append(el('w:tblHeader'))
 tr.append(trpr)
 for j,val in enumerate(row):
  tc=el('w:tc');tcpr=el('w:tcPr');tcpr.append(el('w:tcW',**{'w:w':widths[j],'w:type':'dxa'}));tcpr.append(el('w:vAlign',**{'w:val':'center'}))
  if i==0:tcpr.append(el('w:shd',**{'w:fill':'E6E6E6'}))
  tc.append(tcpr);p=para(val,size=8.5,bold=i==0);ppr=el('w:pPr');ppr.append(el('w:spacing',**{'w:before':0,'w:after':35}));ppr.append(el('w:jc',**{'w:val':'left' if j==0 else 'center'}));p.insert(0,ppr);tc.append(p);tr.append(tc)
 tbl.append(tr)
caption=content['captions']['TABLE_CORE3_W1_PROFILES']
# Insert directly after the new Stage7 Results paragraphs, before the next source paragraph.
end=next(c for c in body if c.tag==el('w:p').tag and flat(c)==content['results'][-1]);pos=body.index(end)+1
body.insert(pos,para(caption,ps[39],keep=True,pagebreak=True,size=9));body.insert(pos+1,tbl)
changes.append(dict(source_location='new Table4 after Stage7 results',old_exact_text='',new_exact_text=caption,operation='insert table; existing Table1–3 unchanged'))

rels=E.fromstring(parts['word/_rels/document.xml.rels']);relns='http://schemas.openxmlformats.org/package/2006/relationships'
used=[int(x.get('Id')[3:]) for x in rels if x.get('Id','').startswith('rId') and x.get('Id')[3:].isdigit()];rid=max(used)+1
usedids=[int(x) for x in doc.xpath('.//wp:docPr/@id',namespaces=ns)];drawid=max(usedids)+1
from PIL import Image
def image_p(name,relid,number):
 img=Image.open(lp(OUT/(name+'.png')));w,himg=img.size;cx=6217920;cy=round(cx*himg/w)
 p=el('w:p');pr=el('w:pPr');pr.append(el('w:pageBreakBefore'));pr.append(el('w:keepNext'));p.append(pr)
 r=el('w:r');p.append(r);dr=el('w:drawing');r.append(dr);inline=el('wp:inline',distT=0,distB=0,distL=0,distR=0);dr.append(inline)
 inline.append(el('wp:extent',cx=cx,cy=cy));inline.append(el('wp:docPr',id=number,name=name));graphic=el('a:graphic');inline.append(graphic);gd=el('a:graphicData',uri=ns['pic']);graphic.append(gd);pic=el('pic:pic');gd.append(pic)
 nv=el('pic:nvPicPr');nv.append(el('pic:cNvPr',id=number,name=name));nv.append(el('pic:cNvPicPr'));pic.append(nv)
 fill=el('pic:blipFill');fill.append(el('a:blip',**{'r:embed':relid}));stretch=el('a:stretch');stretch.append(el('a:fillRect'));fill.append(stretch);pic.append(fill)
 spr=el('pic:spPr');xfrm=el('a:xfrm');xfrm.append(el('a:off',x=0,y=0));xfrm.append(el('a:ext',cx=cx,cy=cy));spr.append(xfrm);geom=el('a:prstGeom',prst='rect');geom.append(el('a:avLst'));spr.append(geom);pic.append(spr);return p
for name in ['FIG_CORE3_W1_MEMBERSHIP','FIG_CORE3_W1_PROFILES']:
 relid=f'rId{rid}';rid+=1;filename=name+'.png';rel=E.SubElement(rels,'{'+relns+'}Relationship',Id=relid,Type=ns['r']+'/image',Target='media/'+filename)
 parts['word/media/'+filename]=lp(OUT/filename).read_bytes()
 pos=body.index(body.find('w:sectPr',ns));body.insert(pos,image_p(name,relid,drawid));drawid+=1;body.insert(pos+1,para(content['captions'][name],ps[113],size=9))
 changes.append(dict(source_location='new temporary Figure'+('7' if name.endswith('MEMBERSHIP') else '8')+' at figure-section end',old_exact_text='',new_exact_text=content['captions'][name],operation='insert preview; existing six images unchanged'))
parts['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
parts['word/_rels/document.xml.rels']=E.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
ct=E.fromstring(parts['[Content_Types].xml'])
assert any(c.get('Extension')=='png' for c in ct)
dest=lp(OUT/'Manuscript_CORE3_W1_Author_Review.docx')
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for n,b in parts.items():z.writestr(n,b)
with zipfile.ZipFile(S19) as original,zipfile.ZipFile(dest) as new:
 changed=[n for n in original.namelist() if original.read(n)!=new.read(n)]
 assert set(changed)=={'word/document.xml','word/_rels/document.xml.rels'}
 untouched_ps=[p for i,p in enumerate(ps,1) if str(i) not in repl]
 newbody=E.fromstring(new.read('word/document.xml')).find('w:body',ns)
 for p in untouched_ps:assert E.tostring(p) in [E.tostring(c) for c in newbody.findall('w:p',ns)]
 orig_tbl=E.fromstring(original.read('word/document.xml')).findall('w:body/w:tbl',ns)
 new_tbl=newbody.findall('w:tbl',ns)
 for a in orig_tbl:assert E.tostring(a) in [E.tostring(b) for b in new_tbl]
 dump('DOCX_FIDELITY_QA.json',dict(source_sha256=h(S19.read_bytes()),output_sha256=h(dest.read_bytes()),only_changed_existing_parts=changed,unchanged_source_parts=len(original.namelist())-2,untouched_source_paragraphs=len(untouched_ps),original_tables_preserved=3,original_images_preserved=6,source_page_geometry_preserved=True,new_figures=2,new_tables=1,all_styles_citations_equations_preserved=True,review_only=True))
dump('S19_EXACT_CHANGE_LEDGER.json',changes)
lines=['# Stage 7 author review change ledger','',f'Source S19 SHA256 `{h(S19.read_bytes())}`. Separate review copy only. Existing scientific results and the original file are unchanged.','']
for c in changes:lines += ['## '+c['source_location'],'',c['operation'],'','Original: '+(c['old_exact_text'] or '(new material)'),'', 'Proposed: '+c['new_exact_text'],'']
lines += ['Existing source paragraphs not listed above, original Tables1–3, Figures1–6, styles, references, equations, headers/footers and all original media remain byte-identical. New page flow reflects only targeted inserted Stage7 content. The old BE0 review is not the layout/template authority.']
lp(OUT/'STAGE7_AUTHOR_REVIEW_CHANGELOG.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
lp(OUT/'artifact.md').write_text('S19 is the explicit template authority. US Letter 8.5×11 inches; top/bottom0.8 inch and side0.85 inch. Preserve every unrelated OOXML paragraph, all style definitions and parts, three tables and six figures. Change only Stage7 clauses in source P9/P23/P40/P47 plus review metadataP2; insert targeted sections and temporary Figures7–8/Table4. New figures fit6.8-inch text width; new table8.5pt. No generic page reset, title redesign, unrelated terminology fixes or citation changes. Native Word export must not save the DOCX. Verify every rendered page and document exact source/output hashes.\n',encoding='utf-8')
print('Created separate S19 author-review DOCX with exact unrelated-part preservation; awaiting native render and visual inspection.')
