"""Assemble an independent contribution-aligned IJDRS artwork configuration.

Reads accepted vector artwork and a read-only author manuscript. No model,
resampling, uncertainty calculation, or scientific figure generator is run.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import fitz
import numpy as np
import pikepdf
from PIL import Image, ImageCms, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / "results/submission_artwork/IJDRS_five_figure"
SOURCE = ROOT / "results/figure_review_s6_main4_20261107"
PORTABLE = ROOT / "results/publication_artwork_20261111"
BASE = "a6847bda22a49b13ba0ef2fa309dfb9cdb994909"
ART_BASE = "68c83459e60ef31f7e86af9155d5a11e1680235d"
MANUSCRIPT_SHA = "39df3b9bf73722ae1dbc88cb015b4ef9ece8322c71bf7b84431476b8150314ac"
DEFAULT_MANUSCRIPT = Path("C:/Users/yinch/Downloads/LA_Grid_Manuscript_Revised.docx")
MM = 72 / 25.4
W = 185 * MM
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
HELPER = Path(__file__).with_name("publication_artwork.py")
spec = importlib.util.spec_from_file_location("portable_artwork", HELPER)
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n",
                    encoding="utf-8", newline="\n")


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def source_pdf(stem):
    return SOURCE / ("Supplement" if stem.startswith("FigS") else "Main") / (stem + ".pdf")


def output_pdf(group, number):
    return DEST / group / (("Fig" if group == "Main" else "FigS") + f"{number:02d}.pdf")


def font_buffers():
    with fitz.open(source_pdf("Fig01")) as doc:
        return (art.font_program(doc, "ArialMT"), art.font_program(doc, "Arial-BoldMT"))


def add_text(page, text, x, y, size=9.5, bold=True, center=False, font_prefix='IJDRS'):
    regular, heavy = FONTS
    buf = heavy if bold else regular
    name = font_prefix+("ArialBold" if bold else "Arial")
    art.insert_publication_font(page, name, buf, text)
    if center:
        x -= fitz.Font(fontbuffer=buf).text_length(text, fontsize=size) / 2
    page.insert_text((x, y), text, fontsize=size, fontname=name, color=(.1, .12, .13))


def save(doc, path, title):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata({"title": title, "creator": "LA Grid IJDRS contribution-aligned artwork"})
    doc.save(path, garbage=4, deflate=True, no_new_id=True)
    doc.close()


def part(stem, panel, clip, x, y, *, title=None, scale=1.0, title_y=None):
    return dict(source=stem, original_panel=panel, clip=list(clip), x=x, y=y,
                scale=scale, title=title, title_y=title_y)


# Clips include axes, uncertainty bars, annotations and legends, never data alone.
# Target positions are points on a 185-mm page; uniform scale is explicit.
LAYOUTS = {
    "Main/Fig02": (225, "Damage-to-service mechanisms and baseline recovery", [
        part("Fig03", "B", (270, 43, 524.4, 215), 1, 28,
             title="A. Initial tract-service distributions"),
        part("Fig03", "E", (285, 414, 524.4, 611.8), 279, 28,
             title="B. Unconstrained mean tract T80"),
        part("Fig03", "C", (0, 239, 524.4, 383), 0, 254,
             title="C. Unconstrained service-loss decomposition"),
        part("Fig04", "A: focal policies", (0, 53, 260, 188), 0, 439,
             title="D. Full-network and fixed-path access"),
        part("Fig04", "B: focal policies", (0, 266, 260, 389), 264, 439,
             title="E. Gain from alternate routes"),
        part("Fig04", "A: line-style key", (164, 27, 370, 42), 159, 404),
        part("Fig04", "A: focal strategy key", (50, 190, 260, 225), 157, 594),
    ]),
    "Main/Fig03": (225, "Restoration performance and distributional trade-offs", [
        part("Fig05", "B", (0, 327, 524.4, 529.8), 0, 24,
             title="A. Service loss and recovery time"),
        part("Fig06", "B", (281, 79, 524.4, 232), 10, 283,
             title="B. Service loss across vulnerability groups"),
        part("Fig06", "D", (378, 307, 524.4, 448), 349, 283,
             title="C. Gini change"),
        part("Fig06", "C", (47, 307, 367, 445), 96, 488,
             title="D. Vulnerability-first paired effects",title_y=456),
        part("Fig06", "C: comparison key", (105, 286, 415, 305), 107, 466),
    ]),
    "Supplement/FigS02": (80, "Damage and Unconstrained recovery-time distributions", [
        part("Fig03", "A", (37, 41, 254, 213), 8, 28,
             title="A. Mean station damage state"),
        part("Fig03", "D", (32, 409, 261, 606), 280, 28,
             title="B. Population-weighted T80"),
    ]),
    "Supplement/FigS04": (105, "Modeled service-availability trajectories", [
        part("Fig05", "A", (0, 23, 524.4, 290), 0, 22,
             title="Service-availability recovery by strategy"),
    ]),
    "Supplement/FigS05": (181, "Additional distributional and spatial comparisons", [
        part("Fig06", "A: strategy key", (65, 0, 516, 53), 30, 7),
        part("Fig06", "A", (14, 80, 265, 247), 135, 88,
             title="A. Overall and Q4 service loss"),
        part("Fig06", "E", (0, 490, 524.4, 706.8), 0, 285,
             title="B. Spatial service-loss changes"),
    ]),
}


def assemble(key, height, title, parts):
    doc = fitz.open()
    page = doc.new_page(width=W, height=height * MM)
    placements = []
    for item in parts:
        path = source_pdf(item["source"])
        clip = fitz.Rect(item["clip"])
        s = item["scale"]
        rect = fitz.Rect(item["x"], item["y"], item["x"] + clip.width*s,
                         item["y"] + clip.height*s)
        assert page.rect.contains(rect), (key, item["original_panel"], rect)
        with fitz.open(path) as source:
            art.place_vector(page, rect, source, clip=clip)
        placements.append({**item, "source_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                           "source_sha256": digest(path), "target": list(rect)})
        if item["title"]:
            add_text(page, item["title"], (rect.x0 + rect.x1)/2,
                     item['title_y'] if item['title_y'] is not None else rect.y0-8,
                     size=9, center=True)
    if key == "Main/Fig03":
        # Four named focal strategies in the quartile plot, not all seven rows of A.
        names = [("Impact-first", "#ff7f00"), ("Hospital-first", "#555555"),
                 ("Degree-first", "#4daf4a"), ("Vulnerability-first", "#a65628")]
        for index,(x, (name, color)) in enumerate(zip([34, 153, 274, 383], names)):
            rgb = tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
            page.draw_line((x, 252), (x+13,252), color=rgb, width=1.2)
            cx,cy=x+6.5,252
            if index==0:page.draw_rect(fitz.Rect(cx-1.6,cy-1.6,cx+1.6,cy+1.6),color=rgb,fill=rgb,width=.4)
            elif index==1:page.draw_circle((cx,cy),1.6,color=rgb,fill=rgb,width=.4)
            else:
                points=([(cx,cy-2),(cx-1.8,cy+1.5),(cx+1.8,cy+1.5)] if index==2 else
                        [(cx,cy-2),(cx-2,cy),(cx,cy+2),(cx+2,cy)])
                shape=page.new_shape();shape.draw_polyline(points);shape.finish(color=rgb,fill=rgb,closePath=True,width=.4);shape.commit()
            add_text(page, name, x+17,254.5,size=7.5,bold=False)
    if key == "Main/Fig02":
        add_text(page,'Time after earthquake (h)',150,586,size=7.5,bold=False,center=True)
    target = DEST / (key + ".pdf")
    save(doc,target,title)
    return dict(pdf=str(target.relative_to(ROOT)).replace("\\", "/"),
                sha256=digest(target), placements=placements)


def workflow():
    source=PORTABLE/"universal/layout_variants/workflow_compact.pdf"
    target=output_pdf("Main",1)
    replacements={"strategies in Figure 5":"strategies in Figure 3",
                  "See Figure 8 for class key":"See Figure 5 for class key"}
    changes=[]
    font=fitz.Font(fontbuffer=FONTS[0])
    encode=lambda text:b''.join(font.has_glyph(ord(c)).to_bytes(2,'big') for c in text)
    patterns={encode(old):(old,new,encode(new)) for old,new in replacements.items()}
    # Edit only the two reference strings in existing text-show operators.
    # Text-only redaction would expand deeply clipped GIS forms unnecessarily.
    with pikepdf.open(source) as doc:
        for obj in doc.objects:
            if not isinstance(obj,pikepdf.Stream):continue
            raw=obj.read_bytes()
            if not any(pattern.hex().encode() in raw.lower() for pattern in patterns):continue
            operations=list(pikepdf.parse_content_stream(obj))
            count=0; output=[]
            for ins in operations:
                op=str(ins.operator)
                operands=list(ins.operands)
                if op in ['TJ','Tj']:
                    values=list(operands[0]) if op=='TJ' else [operands[0]]
                    for i,value in enumerate(values):
                        if not isinstance(value,pikepdf.String):continue
                        data=bytes(value)
                        for pattern,(old,new,replacement) in patterns.items():
                            if pattern in data:
                                assert len(pattern)==len(replacement)
                                data=data.replace(pattern,replacement)
                                changes.append(dict(object=list(obj.objgen),old=old,new=new))
                                count+=1
                        values[i]=pikepdf.String(data)
                    operands[0]=pikepdf.Array(values) if op=='TJ' else values[0]
                    ins=pikepdf.ContentStreamInstruction(operands,ins.operator)
                output.append(ins)
            assert count
            obj.write(pikepdf.unparse_content_stream(output))
        assert Counter(c['old'] for c in changes)==Counter({'strategies in Figure 5':7,'See Figure 8 for class key':1})
        target.parent.mkdir(parents=True,exist_ok=True)
        doc.save(target,compress_streams=True,object_stream_mode=pikepdf.ObjectStreamMode.generate,deterministic_id=True)
    return dict(source=str(source.relative_to(ROOT)).replace("\\", "/"),
                source_sha256=digest(source),pdf=str(target.relative_to(ROOT)).replace("\\", "/"),
                sha256=digest(target),changes=changes,scientific_graphics_changed=False)


FULL_COPIES = {
    "Main/Fig04": "resource_effects", "Main/Fig05": "community_context",
    "Supplement/FigS01": "network_dependencies", "Supplement/FigS03": "source_connectivity",
    "Supplement/FigS06": "damage_geography", "Supplement/FigS07": "restoration_logistics",
    "Supplement/FigS08": "network_recovery", "Supplement/FigS09": "ga_evaluation",
    "Supplement/FigS10": "mapping_gate_sensitivity", "Supplement/FigS11": "facility_limits",
    "Supplement/FigS12": "priority_geography", "Supplement/FigS13": "resource_outcomes",
}


def full_copies():
    registry=json.loads((PORTABLE/"universal/MASTERS.json").read_text())
    rows={r["identity"]:r for r in registry["figures"]}
    result={}
    for key,identity in FULL_COPIES.items():
        row=rows[identity]; source=ROOT/row["pdf"]; target=DEST/(key+".pdf")
        assert digest(source)==row["pdf_sha256"]
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        shutil.copyfile(ROOT/row["png"],target.with_suffix(".png"))
        result[key]=dict(identity=identity,source=row["pdf"],sha256=digest(target),
                         accepted_master=row["accepted_source"],accepted_master_sha256=row["source_sha256"],
                         exact_delivery_bytes=True)
    return result


def exports():
    rows=[]
    prior_path=DEST/'FIGURE_MANIFEST.json'
    previous={r['pdf']:r for r in json.loads(prior_path.read_text())['figures']} if prior_path.exists() else {}
    for pdf in sorted((DEST/"Main").glob("*.pdf"))+sorted((DEST/"Supplement").glob("*.pdf")):
        relative=pdf.relative_to(DEST).as_posix()
        previous_row=previous.get(relative)
        preview=DEST/'Previews'/(pdf.stem+'.png')
        if (previous_row and digest(pdf)==previous_row['pdf_sha256'] and
            all(pdf.with_suffix(ext).exists() and digest(pdf.with_suffix(ext))==previous_row[field]
                for ext,field in [('.png','png_sha256'),('.tif','tiff_sha256')])):
            if not (previous_row.get('preview_sha256') and preview.exists() and digest(preview)==previous_row['preview_sha256']):
                preview.parent.mkdir(parents=True,exist_ok=True)
                subprocess.run(['pdftoppm','-f','1','-l','1','-singlefile','-r','150','-png',str(pdf),str(preview.with_suffix(''))],check=True)
            rows.append(dict(previous_row,preview_sha256=digest(preview)))
            print('Reuse verified derivatives',relative,flush=True)
            continue
        with fitz.open(pdf) as doc:
            page=doc[0]
            if not pdf.with_suffix(".png").exists() or pdf.stem in ["Fig01","Fig02","Fig03","FigS02","FigS04","FigS05"]:
                subprocess.run(['pdftoppm','-f','1','-l','1','-singlefile','-r','600','-png',str(pdf),str(pdf.with_suffix(''))],check=True)
            # Always create a genuine, losslessly encoded TIFF at the native dimensions.
            tiff=pdf.with_suffix(".tif")
            image=Image.open(pdf.with_suffix(".png")).convert("RGB")
            icc=(PORTABLE/"universal/color/srgb.icc").read_bytes()
            image.save(tiff,format="TIFF",compression="tiff_lzw",dpi=(600,600),icc_profile=icc)
            with Image.open(tiff) as restored:
                assert restored.format=="TIFF" and restored.tobytes()==image.tobytes()
            preview=DEST/"Previews"/(pdf.stem+".png")
            preview.parent.mkdir(parents=True,exist_ok=True)
            subprocess.run(['pdftoppm','-f','1','-l','1','-singlefile','-r','150','-png',str(pdf),str(preview.with_suffix(''))],check=True)
            spans=[s for b in page.get_text("dict")["blocks"] for l in b.get("lines",[]) for s in l["spans"] if s["text"].strip()]
            assert all(page.rect.contains(fitz.Rect(s["bbox"])) for s in spans),(pdf,"clipped text")
            fonts=list(art.font_programs(doc))
            assert all(data for _,data in fonts)
            rows.append(dict(figure=pdf.stem,group=pdf.parent.name,pdf=pdf.relative_to(DEST).as_posix(),
                pdf_sha256=digest(pdf),png_sha256=digest(pdf.with_suffix('.png')),
                tiff_sha256=digest(tiff),bytes=pdf.stat().st_size,size_mm=[page.rect.width/MM,page.rect.height/MM],
                minimum_text_pt=min(s['size'] for s in spans),tiff_dpi=600,tiff_roundtrip_identical=True,
                preview_sha256=digest(preview),fonts=sorted(set(s['font'] for s in spans))))
    write_json(DEST/"FIGURE_MANIFEST.json",dict(base=BASE,figures=rows))
    return rows


def caption_records():
    text=(DEST/"CAPTIONS.md").read_text(encoding="utf-8")
    records={}
    for heading,body in re.findall(r"^## ([^\n]+)\n\n(.*?)(?=\n## |\Z)",text,re.M|re.S):
        token=re.match(r"(Supplementary )?Figure (S?\d+)\.",heading)
        assert token,heading
        records[token[2]]=(heading,body.strip())
    assert len(records)==18
    return records


def separate_captions():
    records=caption_records()
    for name,labels,title in [('MAIN_CAPTIONS.md',[str(i) for i in range(1,6)],'IJDRS main-figure captions'),
                              ('SUPPLEMENTARY_CAPTIONS.md',['S'+str(i) for i in range(1,14)],'Proposed supplementary captions')]:
        lines=['# '+title,'']
        for label in labels:
            heading,body=records[label]
            lines.extend(['## '+heading,'',body,''])
        write_text(DEST/name,'\n'.join(lines))


def packets():
    records=caption_records()
    mapping=[]
    for group,stems,file in [("Main",[f"Fig{i:02d}" for i in range(1,6)],"ALL_MAIN_FIGURES_WITH_CAPTIONS.pdf"),
        ("Supplement",[f"FigS{i:02d}" for i in range(1,14)],"ALL_SUPPLEMENT_PROPOSED_WITH_CAPTIONS.pdf")]:
        doc=fitz.open()
        for i,stem in enumerate(stems,1):
            label=str(i) if group=="Main" else "S"+str(i)
            title,body=records[label]
            with fitz.open(DEST/group/(stem+".pdf")) as src:
                width,height=src[0].rect.width,src[0].rect.height
                metrics=fitz.Font(fontbuffer=FONTS[0]); lines=[]; current=''
                for word in body.split():
                    new=(current+' '+word).strip()
                    if metrics.text_length(new,fontsize=9)>width-32:
                        lines.append(current);current=word
                    else:current=new
                if current:lines.append(current)
                page=doc.new_page(width=width,height=height+len(lines)*12+54)
                # Bind page-local caption fonts before importing artwork whose
                # nested resources may contain the same analytical-font names.
                prefix=f'PacketCaption{group}{i}'
                art.insert_publication_font(page,prefix+'Arial',FONTS[0],title+body)
                art.insert_publication_font(page,prefix+'ArialBold',FONTS[1],title+body)
                art.place_vector(page,src[0].rect,src)
                add_text(page,title,16,height+22,size=9,bold=True,font_prefix=prefix)
                for j,line in enumerate(lines): add_text(page,line,16,height+43+j*12,size=9,bold=False,font_prefix=prefix)
                mapping.append(dict(group=group,page=i,figure=stem,pdf_sha256=digest(DEST/group/(stem+'.pdf')),
                                    caption=body))
        save(doc,DEST/file,"IJDRS five-main configuration; supplementary acceptance unverified")
    complete=fitz.open()
    for file in ["ALL_MAIN_FIGURES_WITH_CAPTIONS.pdf","ALL_SUPPLEMENT_PROPOSED_WITH_CAPTIONS.pdf"]:
        with fitz.open(DEST/file) as src: complete.insert_pdf(src)
    save(complete,DEST/"ALL_FIGURES_WITH_CAPTIONS.pdf","IJDRS five-main and proposed supplementary artwork")
    write_json(DEST/"qa/PACKET_REGISTRY.json",mapping)


def crop_qa(layouts):
    rows=[]
    images={};words={}
    def references(path):
        key=digest(path)
        if key not in images:
            preview=DEST/'tmp'/('qa_'+key[:16]+'_144.png')
            preview.parent.mkdir(parents=True,exist_ok=True)
            if not preview.exists():
                subprocess.run(['pdftoppm','-f','1','-l','1','-singlefile','-r','144','-png',str(path),str(preview.with_suffix(''))],check=True)
            with Image.open(preview) as image:images[key]=np.array(image.convert('RGB'))
            if shutil.which('pdftotext'):
                raw=subprocess.check_output(['pdftotext','-bbox','-enc','UTF-8',str(path),'-'])
                tree=ET.fromstring(raw)
                words[key]=[(fitz.Rect(*(float(n.attrib[k]) for k in ['xMin','yMin','xMax','yMax'])),n.text or '')
                            for n in tree.iter() if n.tag.rsplit('}',1)[-1]=='word']
            else:
                # Cache one full-page word inventory; repeated clipped MuPDF
                # extraction is disproportionately slow for nested GIS forms.
                with fitz.open(path) as doc:
                    words[key]=[(fitz.Rect(w[:4]),w[4]) for w in doc[0].get_text('words')]
        return images[key],words[key]
    def clipped_words(entries,rect):
        return Counter(t for box,t in entries if rect.contains((box.x0+box.width/2,box.y0+box.height/2)))
    for key,record in layouts.items():
        with fitz.open(DEST/(key+".pdf")) as target:
            target_image,target_words=references(DEST/(key+'.pdf'))
            for p in record["placements"]:
                if not p['title']:continue
                with fitz.open(ROOT/p['source_path']) as source:
                    clip=fitz.Rect(p['clip']);rect=fitz.Rect(p['target'])
                    assert p['scale']==1
                    source_image,source_words=references(ROOT/p['source_path'])
                    sx0,sy0,sx1,sy1=[round(v*2) for v in clip]
                    tx0,ty0,tx1,ty1=[round(v*2) for v in rect]
                    aa=source_image[sy0:sy1,sx0:sx1]
                    bb=target_image[ty0:ty1,tx0:tx1]
                    candidates=[]
                    for dy in [-1,0,1]:
                        for dx in [-1,0,1]:
                            av=aa;bv=bb
                            ay=max(0,dy)+3;by=max(0,-dy)+3;ax=max(0,dx)+3;bx=max(0,-dx)+3
                            h=min(av.shape[0]-ay,bv.shape[0]-by)-3;w=min(av.shape[1]-ax,bv.shape[1]-bx)-3
                            av=av[ay:ay+h,ax:ax+w];bv=bv[by:by+h,bx:bx+w]
                            delta=np.abs(av.astype(np.int16)-bv.astype(np.int16))
                            candidates.append((float(delta.mean()),float(np.mean(np.max(delta,axis=2)>32)),dx,dy))
                    best=min(candidates)
                    assert best[0]<6 and best[1]<.06,(key,p['original_panel'],best)
                    source_text=clipped_words(source_words,clip)
                    final_text=clipped_words(target_words,rect)
                    assert +source_text==+final_text,(key,p['original_panel'],'text changed',source_text-final_text,final_text-source_text)
                    rows.append(dict(figure=key,source=p['source'],panel=p['original_panel'],
                        mean_absolute_rgb_difference=best[0],fraction_delta_over_32=best[1],
                        alignment_shift_px=list(best[2:]),text_tokens_identical=True,
                        scale=p['scale'],source_sha256=p['source_sha256'],
                        text_extractor='Poppler bbox' if shutil.which('pdftotext') else 'Cached full-page MuPDF word boxes',
                        interpretation='Independent Poppler 144-dpi crop plus word-box checks of source vector placement, not numerical replotting. Bounds/clipping are also visually checked.'))
    write_json(DEST/"qa/PANEL_EQUIVALENCE.json",rows)


def manuscript_text(path):
    assert digest(path)==MANUSCRIPT_SHA,"Different manuscript: review anchors before using this version"
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('word/document.xml'))
        parents={c:p for p in root.iter() for c in p}
        def visible(node):
            result=[]
            for t in node.iter():
                if t.tag not in ["{"+NS['w']+"}t","{"+NS['m']+"}t"]:continue
                parent=t;skip=False
                while parent in parents:
                    parent=parents[parent]
                    if parent.tag in ['{'+NS['w']+'}del','{'+NS['w']+'}moveFrom']:skip=True;break
                if not skip:result.append(t.text or '')
            return ''.join(result)
        paragraphs={f'P{i:03d}':visible(p).strip() for i,p in enumerate(root.findall('./w:body/w:p',NS))}
        full=visible(root)
        caption_tables=[(k,v) for k,v in paragraphs.items() if re.match(r'^Table \d+\.',v)]
        return paragraphs,dict(path=str(path),sha256=digest(path),bytes=path.stat().st_size,
            extraction='Accepted-visible OOXML text: includes insertions; excludes deletions/move-from; no revisions accepted in the file.',
            inserted_elements=len(root.findall('.//w:ins',NS)),deleted_elements=len(root.findall('.//w:del',NS)),
            approximate_visible_word_tokens=len(re.findall(r"\b[\w]+(?:[-'][\w]+)*\b",full)),
            word_count_caution='Token estimate includes table/math text and references; not a certified Word submission word count.',
            numbered_table_captions=caption_tables,
            direct_table_objects=len(root.findall('./w:body/w:tbl',NS)),
            section_4_6_present=any(re.match(r'^4\.6\b',t) for t in paragraphs.values()))


def manuscript_plan(path):
    paragraphs,identity=manuscript_text(path)
    definitions=json.loads((DEST/"SECTION4_ACTIONS.json").read_text())
    records=[]
    for pid,action in definitions.items():
        text=paragraphs[pid];assert text
        records.append(dict(paragraph=pid,source_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
            anchor=text[:155],original_references=re.findall(r'Figures?\s+\d+(?:[A-H])?(?:\s*(?:and|[-,])\s*\d+[A-H]?)?',text),**action))
    expected=[pid for pid,text in paragraphs.items() if 194<int(pid[1:])<222 and text and not re.match(r'^4\.',text)]
    assert set(expected)==set(definitions),(expected,list(definitions))
    contribution=paragraphs['P031']
    write_json(DEST/"qa/MANUSCRIPT_IDENTITY.json",dict(**identity,
        contribution_paragraph_sha256=hashlib.sha256(contribution.encode()).hexdigest(),
        contribution_statement=contribution,research_questions=[paragraphs[p] for p in ['P027','P028','P029']]))
    write_json(DEST/"SECTION4_PARAGRAPH_CROSSWALK.json",dict(manuscript_sha256=MANUSCRIPT_SHA,paragraphs=records))
    lines=['# Section 4 paragraph editing plan','',
        'Read-only source: `LA_Grid_Manuscript_Revised.docx`, SHA256 `'+MANUSCRIPT_SHA+'`. Downloads and WPS copies match. Paragraph IDs are zero-based direct body-paragraph positions in `word/document.xml`, including blanks. Anchors and text hashes are machine-readable. Tracked insertions are included and deleted text excluded for this review; the Word file is untouched.','',
        'The manuscript figure references are not the current master numbers. For example, manuscript Figure 4 means current master Figure 5, not the promoted source-connectivity Figure 4. A global number replacement is unsafe.','',
        '| Paragraph | Subsection / old reference | New evidence | Editorial action | Review class |',
        '|---|---|---|---|---|']
    for r in records:
        lines.append('| '+r['paragraph']+' | '+r['subsection']+'; '+r['old']+' | '+r['new']+' | '+r['action']+' '+r['reason']+' | '+r['review']+' |')
    lines += ['', '## Subsection sequence','',
        '- 4.1 retains reconstruction and assignment evidence, now Supplementary Figure S1; do not delete its methodological justification.',
        '- 4.2 introduces Figure 2 and Supplementary Figures S2/S3; distinguish damage distributions, mechanism decomposition and topological source access. Add a later interpretation of the main dynamic route comparison; no new prose is written here.',
        '- 4.3 introduces Figure 3A and Supplementary Figure S4 trajectories. Keep overall strategy performance distinct from the targeting contrasts in 4.4.',
        '- 4.4 uses Figure 3B-D and Figure 4, then Supplementary Figures S5/S13 for geographic redistribution and absolute resource outcomes. Combine caption-walkthrough passages only after the metric/claim issues are resolved.',
        '- 4.5 retains Figure 5, describing fitted profiles and direct tract-level screening without causal cluster validation or intervention-priority claims.',
        '- No Section 4.6 exists in this author-controlled file. Context/future-work text occurs elsewhere, including conclusion paragraph P234. Do not fabricate a paragraph crosswalk or rewrite it in this round.',
        '', '## Later integration gates','',
        'Scientific-review flags below are not silently fixed by artwork renumbering. The abstract, Section 2.3, Methods, Results, Discussion and Conclusions have not been rewritten. Current end-of-manuscript captions still describe superseded panels/hotspot constructs and must be replaced only during an approved coordinated manuscript update. The new caption file belongs to this separate configuration.',
        '', '## Scientific flags by paragraph','']
    for r in records:
        if r.get('flag'):lines.append('- **'+r['paragraph']+'**: '+r['flag'])
    write_text(DEST/"SECTION4_EDITING_PLAN.md",'\n'.join(lines))


def provenance():
    rows=[]
    for path in sorted(SOURCE.glob('Main/*'))+sorted(SOURCE.glob('Supplement/*')):
        if path.suffix not in ['.pdf','.png']:continue
        rel=path.relative_to(ROOT).as_posix()
        blob=subprocess.check_output(['git','show',ART_BASE+':'+rel],cwd=ROOT)
        oid=re.search(rb'oid sha256:([0-9a-f]{64})',blob).group(1).decode()
        assert digest(path)==oid,(rel,'master changed')
        rows.append(dict(path=rel,sha256=oid,bytes=path.stat().st_size))
    assert len(rows)==32
    write_json(DEST/"qa/SOURCE_IDENTITIES.json",dict(starting_commit=BASE,accepted_artwork_commit=ART_BASE,
        builder_sha256=digest(__file__),export_helper_sha256=digest(HELPER),master_files=rows,
        original_captions_sha256=digest(SOURCE/'MANUSCRIPT_FACING_CAPTIONS.md'),
        source_manifest_sha256=digest(SOURCE/'FIGURE_MANIFEST.csv'),scientific_calculations_run=False))


def links():
    lines=['# Individual IJDRS artwork','',
        'Five main figures and thirteen proposed supplementary figures. Supplementary acceptance/count must be confirmed with IJDRS. All PNG/TIFF files are caption-free. The accepted eight-main/eight-supplement masters remain unchanged.','',
        '| Figure | Vector PDF | PNG 600 dpi | TIFF 600 dpi |','|---|---|---|---|']
    for group,n in [('Main',5),('Supplement',13)]:
        for i in range(1,n+1):
            stem=('Fig' if group=='Main' else 'FigS')+f'{i:02d}'
            lines.append(f'| {stem} | [PDF]({group}/{stem}.pdf) | [PNG]({group}/{stem}.png) | [TIFF]({group}/{stem}.tif) |')
    write_text(DEST/'INDIVIDUAL_FIGURES.md','\n'.join(lines))


def panel_crosswalk():
    rows=[]
    def add(original,panel,targets,reason):
        rows.append(dict(original_figure=original,original_panel=panel,ijdrs_targets=targets,reason=reason))
    add('1','all five stages',['Figure 1'],'Accepted compact workflow; only internal figure pointers change.')
    for p in 'ABCD':add('2',p,['Supplementary Figure S1'+p],'Complete reconstruction and assignment support retained.')
    for p,target in {'A':'Supplementary Figure S2A','B':'Figure 2A','C':'Figure 2C','D':'Supplementary Figure S2B','E':'Figure 2B'}.items():
        add('3',p,[target],'Mechanism/initial/geographic evidence in main; distribution diagnostics retained separately.')
    add('4','A',['Figure 2D (focal strategies)','Supplementary Figure S3A (complete)'],'Full-network/fixed-path comparison; full policy context deliberately retained in S3.')
    add('4','B',['Figure 2E (focal strategies)','Supplementary Figure S3B (complete)'],'Alternate-route gain; full policy context deliberately retained in S3.')
    for p in 'CD':add('4',p,['Supplementary Figure S3'+p],'Conditional station diagnostics remain distinct from dynamic service quantities.')
    add('5','A',['Supplementary Figure S4'],'All trajectories retained; main figure uses compact absolute outcomes.')
    add('5','B',['Figure 3A'],'All seven strategy rows and all three burden outcomes plus T80 retained.')
    for p,target in {'A':'Supplementary Figure S5A','B':'Figure 3B','C':'Figure 3D','D':'Figure 3C','E':'Supplementary Figure S5B'}.items():
        add('6',p,[target],'Preserve targeting, signed/absolute separation, Gini and geographic redistribution as distinct evidence.')
    for p in 'ABCDEFGH':add('7',p,['Figure 4'+p],'All resource outcomes and original uncertainty conventions retained.')
    for p in 'ABCD':add('8',p,['Figure 5'+p],'All class information, seven-coordinate profiles and direct tract-level map retained.')
    for i in range(1,9):add('S'+str(i),'all',['Supplementary Figure S'+str(i+5)],'Complete original supplementary artwork retained without panel deletion.')
    write_json(DEST/'FIGURE_PANEL_CROSSWALK.json',dict(base=BASE,manuscript_sha256=MANUSCRIPT_SHA,
        main_figures=5,proposed_supplementary_figures=13,panel_mappings=rows,
        manuscript_numbering_warning='Manuscript Figure 4/5/6/7 corresponds to current masters 5/6/7/8, not a global one-to-one renumbering.'))
    lines=['# Accepted-master to IJDRS panel crosswalk','',
        'The source master numbering below is not the numbering inside the revised Word file. Use the paragraph-level manuscript plan for that separate mapping. All original captions remain unchanged.','',
        '| Original figure/panel | IJDRS destination | Reason |','|---|---|---|']
    for row in rows:lines.append('| '+row['original_figure']+' / '+row['original_panel']+' | '+'; '.join(row['ijdrs_targets'])+' | '+row['reason']+' |')
    write_text(DEST/'FIGURE_PANEL_CROSSWALK.md','\n'.join(lines))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manuscript',type=Path,default=DEFAULT_MANUSCRIPT)
    parser.add_argument('--artwork-only',action='store_true',help='Reuse the recorded manuscript plan without claiming a fresh DOCX review.')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args()
    fingerprint=hashlib.sha256(json.dumps({str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),HELPER,
        DEST/'CAPTIONS.md',PORTABLE/'universal/MASTERS.json',
        PORTABLE/'universal/layout_variants/workflow_compact.pdf']},sort_keys=True).encode()).hexdigest()
    cache=DEST/'qa/BUILD_CACHE.json'
    if cache.exists() and not args.force:
        old=json.loads(cache.read_text())
        if old['fingerprint']==fingerprint and all((DEST/p).exists() and digest(DEST/p)==h for p,h in old['outputs'].items()):
            provenance()
            if not args.artwork_only:manuscript_plan(args.manuscript)
            else:print('Artwork-only reproduction: the registered manuscript review is retained, not refreshed.')
            panel_crosswalk();separate_captions()
            print('Verified artwork cache reused; source preservation rechecked. '+
                  ('Registered manuscript review retained without a new DOCX check.' if args.artwork_only else
                   'Manuscript identity rechecked against the supplied DOCX.'));return
    global FONTS
    FONTS=font_buffers()
    provenance()
    if not args.artwork_only:manuscript_plan(args.manuscript)
    else:
        assert (DEST/'qa/MANUSCRIPT_IDENTITY.json').exists() and (DEST/'SECTION4_PARAGRAPH_CROSSWALK.json').exists()
        print('Artwork-only reproduction: the registered manuscript review is retained, not refreshed.')
    layouts={}
    for key,(height,title,parts) in LAYOUTS.items():
        print('Assemble',key,flush=True)
        layouts[key]=assemble(key,height,title,parts)
    wf=workflow();copies=full_copies()
    write_json(DEST/'qa/ASSEMBLY_REGISTRY.json',dict(layouts=layouts,workflow=wf,copies=copies))
    exports();packets();crop_qa(layouts);links();panel_crosswalk();separate_captions()
    outputs={p.relative_to(DEST).as_posix():digest(p) for p in DEST.rglob('*') if p.is_file() and
             p.suffix.lower() in ['.pdf','.png','.tif'] and 'tmp' not in p.relative_to(DEST).parts}
    write_json(cache,dict(fingerprint=fingerprint,outputs=outputs,
        note='Only declared artwork outputs are cached; manual editorial records are not render dependencies. --force rebuilds from accepted vectors.'))
    print('Five-main artwork configuration built; no source manuscript or master edited.',flush=True)


if __name__=='__main__':
    main()
