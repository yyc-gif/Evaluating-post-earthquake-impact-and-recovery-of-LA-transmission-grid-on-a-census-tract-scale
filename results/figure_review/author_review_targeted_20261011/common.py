"""Read-only baseline access and isolated vector-artwork review utilities."""
from pathlib import Path
import hashlib,json,subprocess,re
import fitz

PKG=Path(__file__).resolve().parent
ROOT=PKG.parents[2]
OUTER=ROOT.parent
ORIGINAL=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
BASE='031d2c675f8e7d58035d27448be040b809ced086'
MM=72/25.4

def lp(p):
    path = str(Path(p).resolve())
    return path if path.startswith('\\\\?\\') else '\\\\?\\' + path

def sha(p):
    h=hashlib.sha256()
    with open(lp(p),'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def git(*args,root=ROOT):
    return subprocess.check_output(['git','-C',str(root),*args])

def source(rel):
    blob=git('show',f'{BASE}:{rel}')
    match=re.search(rb'oid sha256:([0-9a-f]{64})',blob)
    expected=match.group(1).decode() if match else hashlib.sha256(blob).hexdigest()
    for directory in [ORIGINAL,ROOT,OUTER/'_gpc13',OUTER/'_gri11',OUTER/'_ad11']:
        p=directory/rel
        try:
            if sha(p)==expected:return p,expected
        except (FileNotFoundError,OSError):pass
    # Validated object store payload, with no checkout writes.
    common=git('rev-parse','--path-format=absolute','--git-common-dir').decode().strip()
    p=Path(common)/'lfs/objects'/expected[:2]/expected[2:4]/expected
    if p.exists() and sha(p)==expected:return p,expected
    raise FileNotFoundError(f'No verified baseline payload: {rel}; {expected}')

def open_source(rel):
    p,h=source(rel)
    return fitz.open(stream=open(lp(p),'rb').read(),filetype='pdf'),h

def dump(name,data):
    with open(lp(PKG/name),'w',encoding='utf-8') as f:json.dump(data,f,indent=2,ensure_ascii=False)

def streams(doc):
    return sorted({x for p in doc for x in p.get_contents()}|{x for x in range(1,doc.xref_length()) if doc.xref_is_stream(x) and doc.xref_get_key(x,'Subtype')[1]=='/Form'})

def preview(doc,name,dpi=160):
    Path(lp((PKG/name).parent)).mkdir(parents=True,exist_ok=True)
    p=doc[0];pix=p.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
    pix.set_dpi(dpi,dpi);pix.save(lp(PKG/name))

def spans(page):
    return [s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]

def text(page,x,y,value,size=8,bold=False,center=False,color=(.1,.1,.1),font_prefix='Author'):
    fontpath='C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'
    fname=font_prefix+('ArialBold' if bold else 'Arial')
    page.insert_font(fontname=fname,fontfile=fontpath)
    font=fitz.Font(fontfile=fontpath)
    px=x*MM-(font.text_length(value,fontsize=size)/2 if center else 0)
    page.insert_text((px,y*MM),value,fontname=fname,fontsize=size,color=color)

def export(doc,name):
    path=PKG/(name+'.pdf');Path(lp(path.parent)).mkdir(parents=True,exist_ok=True);doc.save(lp(path),deflate=True,garbage=4)
    check=fitz.open(lp(path));preview(check,name+'.png',600);preview(check,'qa/'+name+'.png')
    return {'file':name+'.pdf','sha256':sha(path),'size_mm':[check[0].rect.width/MM,check[0].rect.height/MM],
            'min_font_pt':min(s['size'] for s in spans(check[0])),'image_count':len(check[0].get_images())}

