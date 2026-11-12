"""Journal-neutral PDF preflight and derived exports; never run scientific models."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import io
import importlib.metadata
import inspect
import json
import math
from pathlib import Path
import re
import sys
import subprocess
import unicodedata

import fitz
import numpy as np
import pikepdf
from PIL import Image, ImageCms, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'results/figure_review_s6_main4_20261107'
DEST = ROOT / 'results/publication_artwork_20261111'
BASE = '68c83459e60ef31f7e86af9155d5a11e1680235d'
ITEMS = [
    ('Fig01', 'workflow'), ('Fig02', 'network_dependencies'),
    ('Fig03', 'damage_service'), ('Fig04', 'source_connectivity'),
    ('Fig05', 'strategy_performance'), ('Fig06', 'distributional_effects'),
    ('Fig07', 'resource_effects'), ('Fig08', 'community_context'),
    ('FigS01', 'damage_geography'), ('FigS02', 'restoration_logistics'),
    ('FigS03', 'network_recovery'), ('FigS04', 'ga_evaluation'),
    ('FigS05', 'mapping_gate_sensitivity'), ('FigS06', 'facility_limits'),
    ('FigS07', 'priority_geography'), ('FigS08', 'resource_outcomes')]
PRIMARY = ['workflow', 'damage_service', 'source_connectivity',
           'strategy_performance', 'distributional_effects']
SUPPLEMENT = [key for _, key in ITEMS if key not in PRIMARY]
# Measured blank strips contain only frame edges or straight connector stems.
BANDS = [(57, 62), (92, 97), (224, 234), (240, 248), (254, 260),
         (302, 313), (375, 391), (418, 430), (437, 441), (596, 598), (743, 748)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def original(stem):
    return SOURCE / ('Supplement' if stem.startswith('FigS') else 'Main') / (stem+'.pdf')


def relative(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def render_image(page, dpi):
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


def place_vector(page, rectangle, source, clip=None, pno=0):
    """Unrotated PDF placement without exponential shared-resource scans.

    The pinned PyMuPDF public wrapper recursively inventories every nested
    resource merely to choose a name. Use the same native graft operation,
    with a reserved, checked unique root name; retain vectors and transforms.
    """
    doc=page.parent
    target=fitz.Rect(rectangle)*~page.transformation_matrix
    src=source[pno]
    crop=(src.rect if clip is None else src.rect & fitz.Rect(clip))*~src.transformation_matrix
    assert not target.is_empty and not crop.is_empty
    sx,sy=target.width/crop.width,target.height/crop.height
    matrix=(sx,0,0,sy,target.x0-sx*crop.x0,target.y0-sy*crop.y0)
    name='pubart'+str(doc.xref_length())
    assert '/'+name not in doc.xref_get_key(page.xref,'Resources/XObject')[1]
    identity=source._graft_id
    graft=doc.Graftmaps.get(identity)
    if graft is None:
        graft=fitz.Graftmap(doc)
        doc.Graftmaps[identity]=graft
    key=(identity,pno)
    page.wrap_contents()
    xref=page._show_pdf_page(src,overlay=True,matrix=matrix,
        xref=doc.ShownPages.get(key,0),oc=0,clip=crop,graftmap=graft,_imgname=name)
    doc.ShownPages[key]=xref
    return dict(xref=xref,resource_name=name)


def strip_source_document(source_bytes,sections):
    """Prune only Form invocations provably outside each strip's hard bounds.

    Leaf GIS/text/image streams are reused, never simplified or re-encoded.
    Conservatively expanded bounds prevent a clipping-edge false exclusion.
    """
    stats=Counter()
    with pikepdf.open(io.BytesIO(source_bytes)) as pdf:
        base=pdf.pages[0]
        media=[str(v) for v in base.MediaBox]
        assert float(media[0])==float(media[1])==0 and int(base.get('/Rotate',0))==0
        width,height=float(media[2]),float(media[3])
        resources=base.Resources
        parsed={}
        memo={}

        def rewrite(operations,res,transform,clip,depth=0):
            assert depth<64
            current=fitz.Matrix(transform)
            stack=[]
            result=[]
            cloned_res=pikepdf.Dictionary(dict(res.items()))
            objects=pikepdf.Dictionary(dict(res.get('/XObject',{}).items()))
            changed=False
            for ins in operations:
                op=str(ins.operator)
                if op=='q':stack.append(fitz.Matrix(current))
                elif op=='Q':current=stack.pop()
                elif op=='cm':current=fitz.Matrix(*map(float,ins.operands))*current
                elif op=='Do':
                    name=ins.operands[0]
                    child=res.get('/XObject',{}).get(name)
                    if child is not None and child.get('/Subtype')=='/Form':
                        ctm=fitz.Matrix(*map(float,child.get('/Matrix',[1,0,0,1,0,0])))*current
                        bounds=fitz.Rect(list(map(float,child.BBox)))*ctm
                        bounds+=(-.02,-.02,.02,.02)
                        if not bounds.intersects(clip):
                            stats['omitted_outside_form_calls']+=1
                            changed=True
                            continue
                        if not clip.contains(bounds):
                            own=child.get('/Resources',res)
                            has_forms=any(x.get('/Subtype')=='/Form' for x in own.get('/XObject',{}).values())
                            if has_forms:
                                key=(child.objgen,tuple(ctm),tuple(clip & bounds))
                                cached=memo.get(key) if '/Resources' in child else None
                                if cached is None:
                                    if child.objgen not in parsed:
                                        parsed[child.objgen]=list(pikepdf.parse_content_stream(child))
                                    ops2,res2,different=rewrite(parsed[child.objgen],own,ctm,clip & bounds,depth+1)
                                    cached=child
                                    if different:
                                        cached=pdf.make_stream(pikepdf.unparse_content_stream(ops2))
                                        for k,v in child.items():
                                            if k not in ['/Length','/Filter','/DecodeParms']:cached[k]=v
                                        cached.Resources=res2
                                        stats['new_small_parent_forms']+=1
                                    if '/Resources' in child:memo[key]=cached
                                if cached.objgen!=child.objgen:
                                    new_name=pikepdf.Name('/PubStrip'+str(len(objects)))
                                    assert new_name not in objects
                                    objects[new_name]=cached
                                    ins=pikepdf.ContentStreamInstruction([new_name],pikepdf.Operator('Do'))
                                    changed=True
                            else:stats['reused_unmodified_leaf_calls']+=1
                result.append(ins)
            assert not stack
            contextual=bool(res.get('/Pattern')) or any(
                font.get('/Subtype')=='/Type3' for font in res.get('/Font',{}).values())
            contextual=contextual or any(gs.get('/SMask') not in [None,pikepdf.Name('/None')]
                for gs in res.get('/ExtGState',{}).values())
            if not contextual:
                used={ins.operands[0] for ins in result if str(ins.operator)=='Do'}
                unused=set(objects.keys())-used
                for name in unused:del objects[name]
                if unused:
                    stats['unused_xobject_references_removed']+=len(unused)
                    changed=True
            cloned_res.XObject=objects
            return result,cloned_res,changed

        operations=list(pikepdf.parse_content_stream(base))
        for section in sections:
            top,bottom=section['source_y']
            clip=fitz.Rect(0,height-bottom,width,height-top)
            ops,res,_=rewrite(operations,resources,fitz.Matrix(1,0,0,1,0,0),clip)
            page=pdf.add_blank_page(page_size=(width,height))
            page.MediaBox=pikepdf.Array(base.MediaBox)
            page.Resources=res
            page.Contents=pdf.make_stream(pikepdf.unparse_content_stream(ops))
        del pdf.pages[0]
        buffer=io.BytesIO()
        pdf.save(buffer,compress_streams=True,object_stream_mode=pikepdf.ObjectStreamMode.generate,deterministic_id=True)
    return buffer.getvalue(),dict(stats),media


def canonicalize_strip_transforms(output,sections,media):
    # Decimal PDF coordinates avoid tiny unintended float32 scale/shift errors.
    width,height=Decimal(media[2]),Decimal(media[3])
    new_height=Decimal(str(round(sections[-1]['target_y'][1],2)))
    with pikepdf.open(output,allow_overwriting_input=True) as pdf:
        page=pdf.pages[0]
        page.MediaBox=pikepdf.Array([0,0,width,new_height])
        for s in sections:
            top,bottom=[Decimal(str(round(v,2))) for v in s['source_y']]
            target_top=Decimal(str(round(s['target_y'][0],2)))
            form=page.Resources.XObject['/'+s['resource_name']]
            form.Matrix=pikepdf.Array([1,0,0,1,0,new_height-height+top-target_top])
            form.BBox=pikepdf.Array([0,height-bottom,width,height-top])
        pdf.save(output,compress_streams=True,object_stream_mode=pikepdf.ObjectStreamMode.generate,deterministic_id=True)


def text_inventory(page):
    return Counter(' '.join(page.get_text().split()).split())


def drawing_streams(path):
    with fitz.open(path) as doc:
        ids = set(doc[0].get_contents())
        ids.update(x for x in range(1, doc.xref_length())
                   if doc.xref_get_key(x, 'Subtype')[1] == '/Form')
        return {sha(doc.xref_stream(x)) for x in ids}


def unicode_maps(path):
    records=set()
    with pikepdf.open(path) as pdf:
        for obj in pdf.objects:
            if not isinstance(obj,pikepdf.Dictionary) or obj.get('/Type')!='/Font':
                continue
            # CID descendants hold glyph programs; the Type0 parent owns the
            # character-to-Unicode mapping. Subsetting may rename descendants.
            if str(obj.get('/Subtype')).startswith('/CIDFontType'):
                continue
            cmap=obj.get('/ToUnicode')
            encoding=obj.get('/Encoding')
            encoded=sha(encoding.read_bytes()) if isinstance(encoding,pikepdf.Stream) else str(encoding)
            family=re.sub(r'^[A-Z]{6}\+','',str(obj.get('/BaseFont')).lstrip('/'))
            records.add((family,str(obj.get('/Subtype')),encoded,
                         sha(cmap.read_bytes()) if isinstance(cmap,pikepdf.Stream) else str(cmap)))
    return records


def font_programs(doc):
    # Traverse unique PDF objects, not every path through shared GIS resources.
    # Type0 parents own the font encoding; CID descendants are not new fonts.
    for xref in range(1,doc.xref_length()):
        if doc.xref_get_key(xref,'Type')[1]!='/Font':
            continue
        if doc.xref_get_key(xref,'Subtype')[1].startswith('/CIDFontType'):
            continue
        name=doc.xref_get_key(xref,'BaseFont')[1].lstrip('/')
        yield name,doc.extract_font(xref)[3]


def font_program(doc, name):
    aliases={'ArialMT':{'ArialMT','Arial Regular'},
             'Arial-BoldMT':{'Arial-BoldMT','Arial Bold'}}
    candidates=[data for family,data in font_programs(doc)
        if family.split('+')[-1] in aliases.get(name,{name}) and data]
    for data in sorted(candidates,key=len,reverse=True):
        font=fitz.Font(fontbuffer=data)
        if all(font.has_glyph(c) for c in range(32,127)):
            return data
    raise ValueError('No embedded full-coverage font for '+name)


def insert_publication_font(page, name, buffer, text=''):
    """Preserve intended Unicode for glyph aliases such as space/NBSP."""
    xref=page.insert_font(fontname=name,fontbuffer=buffer)
    font=fitz.Font(fontbuffer=buffer)
    mapping={}
    for cp in sorted(set(range(32,127)) | {ord(c) for c in text if c not in '\r\n\t'}):
        gid=font.has_glyph(cp)
        assert gid,(name,hex(cp))
        if gid in mapping and mapping[gid]!=cp:
            assert {mapping[gid],cp} in [{32,160},{45,173}],(name,gid,mapping[gid],cp)
            continue
        mapping[gid]=cp
    rows=['/CIDInit /ProcSet findresource begin','12 dict begin','begincmap',
        '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
        '/CMapName /PublicationUnicode def','/CMapType 2 def',
        '1 begincodespacerange','<0000> <FFFF>','endcodespacerange']
    entries=sorted(mapping.items())
    for start in range(0,len(entries),100):
        chunk=entries[start:start+100]
        rows.append(f'{len(chunk)} beginbfchar')
        rows.extend(f'<{gid:04X}> <{chr(cp).encode("utf-16-be").hex().upper()}>' for gid,cp in chunk)
        rows.append('endbfchar')
    rows.extend(['endcmap','CMapName currentdict /CMap defineresource pop','end','end'])
    kind,value=page.parent.xref_get_key(xref,'ToUnicode')
    assert kind=='xref'
    page.parent.update_stream(int(value.split()[0]),('\n'.join(rows)+'\n').encode('ascii'))
    return xref


def equivalent(source, derived, dpi=600):
    with fitz.open(source) as a, fitz.open(derived) as b:
        assert a[0].rect == b[0].rect
        missing_a={name for name,data in font_programs(a) if not data}
        missing_b={name for name,data in font_programs(b) if not data}
        assert missing_a==missing_b
        for resolution in sorted({150, dpi}):
            y = b[0].get_pixmap(dpi=resolution, alpha=False)
            if resolution==600 and source.with_suffix('.png').exists():
                with Image.open(source.with_suffix('.png')) as original_png:
                    expected=original_png.convert('RGB')
                    assert expected.size==(y.width,y.height)
                    assert expected.tobytes()==y.samples, f'Accepted PNG mismatch: {derived}'
            else:
                x = a[0].get_pixmap(dpi=resolution, alpha=False)
                assert (x.width, x.height) == (y.width, y.height)
                assert x.samples == y.samples, f'Render mismatch at {resolution} dpi: {derived}'
    assert drawing_streams(source) == drawing_streams(derived)
    assert unicode_maps(source)==unicode_maps(derived)
    return dict(pixel_identical_dpi=sorted({150, dpi}), text_operators_and_unicode_maps_identical=True,
                drawing_stream_set_identical=True,
                font_embedding_preserved=True,unembedded_font_names=sorted(missing_b),
                raster_reference_600dpi='Accepted SHA-bound PNG counterpart when present; direct PDF render otherwise')


def source_files():
    return sorted(SOURCE.glob('Main/*.pdf')) + sorted(SOURCE.glob('Supplement/*.pdf'))


def object_inventory(path):
    with fitz.open(path) as doc:
        page = doc[0]
        fontfiles = set()
        for xref in range(1, doc.xref_length()):
            obj = doc.xref_object(xref, compressed=True)
            if '/FontDescriptor' in obj or '/Type/FontDescriptor' in obj:
                for key in ['FontFile', 'FontFile2', 'FontFile3']:
                    typ, val = doc.xref_get_key(xref, key)
                    if typ == 'xref':
                        fontfiles.add(int(val.split()[0]))
        streams = []
        totals = Counter()
        signatures = defaultdict(list)
        for xref in range(1, doc.xref_length()):
            if not doc.xref_is_stream(xref):
                continue
            subtype = doc.xref_get_key(xref, 'Subtype')[1]
            kind = ('image' if subtype == '/Image' else 'form' if subtype == '/Form'
                    else 'font' if xref in fontfiles else 'content_or_other')
            raw = doc.xref_stream_raw(xref)
            entry = dict(xref=xref, kind=kind, stored_bytes=len(raw), sha256=sha(raw))
            streams.append(entry)
            totals[kind] += len(raw)
            signatures[(kind, entry['sha256'])].append(entry)
        duplicates = [dict(kind=k[0], count=len(v), bytes_each=v[0]['stored_bytes'],
                           potential_raw_duplicate_bytes=(len(v)-1)*v[0]['stored_bytes'])
                      for k, v in signatures.items() if len(v) > 1]
        spans = [s for b in page.get_text('dict')['blocks'] for line in b.get('lines', [])
                 for s in line['spans'] if s['text'].strip()]
        images = []
        for im in page.get_images(full=True):
            xref, _, width, height = im[:4]
            rects = page.get_image_rects(xref)
            dpi = [[width*72/box.width, height*72/box.height] for box in rects
                   if box.width and box.height]
            images.append(dict(xref=xref, pixels=[width, height], uses=len(rects),
                effective_dpi_range=([np.min(dpi, axis=0).tolist(), np.max(dpi, axis=0).tolist()] if dpi else []),
                stored_bytes=len(doc.xref_stream_raw(xref))))
        return dict(figure=path.stem, source=path.relative_to(ROOT).as_posix(),
            sha256=sha(path.read_bytes()), bytes=path.stat().st_size,
            width_mm=page.rect.width*25.4/72, height_mm=page.rect.height*25.4/72,
            xrefs=doc.xref_length(), stream_count=len(streams), stream_bytes=dict(totals),
            largest_streams=sorted(streams, key=lambda x:x['stored_bytes'], reverse=True)[:15],
            raw_duplicate_streams=duplicates,
            potential_raw_duplicate_bytes=sum(x['potential_raw_duplicate_bytes'] for x in duplicates),
            images=images, min_font_pt=min(x['size'] for x in spans),
            fonts=sorted({x['font'] for x in spans}),
            internal_figure_references=re.findall(r'(?:Supplementary )?Fig(?:ure)?\.?\s+S?\d+',page.get_text()),
            metadata=doc.metadata,
            unembedded_fonts=sorted({name for name,data in font_programs(doc) if not data}),
            clipped_text=[s['text'] for s in spans if not (page.rect+(-.5,-.5,.5,.5)).contains(fitz.Rect(s['bbox']))])


def audit():
    records = []
    for path in source_files():
        record = object_inventory(path)
        records.append(record)
        print(path.stem, round(record['bytes']/1048576, 2), 'MiB', record['stream_bytes'], flush=True)
    assert len(records) == 16
    dump(DEST/'qa/OBJECT_PREFLIGHT.json', dict(baseline=BASE, figures=records,
        note='Stored stream bytes are counted once per xref. Raw duplicate bytes are a diagnostic upper bound, not proof that dictionaries/resources can safely be merged. Image bounds may extend beyond clipping paths.'))


def prune_resources(pdf):
    counts = Counter()
    contexts = [p.obj for p in pdf.pages]
    contexts += [o for o in pdf.objects if isinstance(o, pikepdf.Stream)
                 and o.get('/Subtype') == '/Form']
    operators = {'Do':'/XObject', 'Tf':'/Font', 'gs':'/ExtGState',
                 'cs':'/ColorSpace', 'CS':'/ColorSpace', 'sh':'/Shading',
                 'scn':'/Pattern', 'SCN':'/Pattern', 'BDC':'/Properties', 'DP':'/Properties'}
    for ctx in contexts:
        resources = ctx.get('/Resources')
        if resources is None:
            continue
        used = defaultdict(set)
        try:
            content = pikepdf.Page(ctx) if ctx.get('/Type') == '/Page' else ctx
            for operands, operator in pikepdf.parse_content_stream(content):
                category = operators.get(str(operator))
                if category:
                    used[category].update(str(x) for x in operands if isinstance(x, pikepdf.Name))
        except (pikepdf.PdfError, ValueError):
            counts['contexts_not_pruned'] += 1
            continue
        # Copy dictionaries: source resources can be shared by several forms.
        replacement = pikepdf.Dictionary(resources)
        for category in set(operators.values()):
            table = resources.get(category)
            if table is None:
                continue
            filtered = pikepdf.Dictionary({k:v for k,v in table.items() if str(k) in used[category]})
            counts[category] += len(table) - len(filtered)
            replacement[category] = filtered
        ctx['/Resources'] = replacement
    return dict(counts)


def optimize(path, output, subset=True):
    output.parent.mkdir(parents=True, exist_ok=True)
    pikepdf.settings.set_flate_compression_level(9)
    with pikepdf.open(path) as pdf:
        removed = prune_resources(pdf)
        fontfiles = {}
        duplicate_fonts = 0
        for obj in pdf.objects:
            if not isinstance(obj, pikepdf.Dictionary) or obj.get('/Type') != '/FontDescriptor':
                continue
            for key in ['/FontFile', '/FontFile2', '/FontFile3']:
                stream = obj.get(key)
                if stream is None:
                    continue
                identity = (key, str(stream.get('/Subtype')), sha(stream.read_bytes()))
                if identity in fontfiles:
                    obj[key] = fontfiles[identity]
                    duplicate_fonts += 1
                else:
                    fontfiles[identity] = stream
        buffer = io.BytesIO()
        pdf.save(buffer, compress_streams=True, recompress_flate=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate, deterministic_id=True)
    with fitz.open(stream=buffer.getvalue(), filetype='pdf') as pdf:
        font_subset_bytes = pdf.subset_fonts() if subset else None
        packed = pdf.tobytes(garbage=4, deflate=True, no_new_id=True)
    with pikepdf.open(io.BytesIO(packed)) as pdf:
        pdf.save(output, compress_streams=True, recompress_flate=True,
                 object_stream_mode=pikepdf.ObjectStreamMode.generate, deterministic_id=True)
    return dict(before_bytes=path.stat().st_size, after_bytes=output.stat().st_size,
                pruned_resource_entries=removed, duplicate_font_references=duplicate_fonts,
                font_subset_report=font_subset_bytes,
                font_subsetting=subset,
                method='Resource pruning, identical font-program sharing, font subsetting, lossless level-9 QPDF compression. No image recompression or path simplification.')


def compact(ijdrs=False):
    source = original('Fig01')
    code_sha=sha(Path(__file__).read_bytes())
    qa_path=DEST/('qa/IJDRS_WORKFLOW_REFERENCE_QA.json' if ijdrs else 'qa/COMPACT_LAYOUT_QA.json')
    output=DEST/('tmp/workflow_ijdrs_references.pdf' if ijdrs else 'universal/layout_variants/workflow_compact.pdf')
    if qa_path.exists() and output.exists() and output.with_suffix('.png').exists():
        previous=json.loads(qa_path.read_text())
        if (previous.get('exporter_sha256')==code_sha and previous['source_sha256']==sha(source.read_bytes())
                and previous['output_sha256']==sha(output.read_bytes())
                and previous.get('png_sha256')==sha(output.with_suffix('.png').read_bytes())):
            print('Reuse verified compact workflow', 'IJDRS' if ijdrs else 'universal',flush=True)
            return output
    # Snap translations to integral pixels at both 150 and 600 dpi.
    bands = [(math.ceil(a/.48)*.48, math.floor(b/.48)*.48) for a,b in BANDS]
    image = np.array(Image.open(source.with_suffix('.png')).convert('RGB'))
    mask = np.any(image < 245, axis=2)
    for x in [8.5, 9.5, 10.5, 255.9, 256.9, 267.6, 268.6, 514.9, 515.9, 132, 392, 262.2]:
        mask[:, round((x-1.6)*600/72):round((x+1.6)*600/72)] = False
    for a,b in bands:
        assert not mask[round(a*600/72):round(b*600/72)].any(), (a,b)
    with fitz.open(source) as src:
        source_page=src[0]
        tp=source_page.get_textpage(flags=fitz.TEXTFLAGS_DICT)
        words_before=Counter(source_page.get_text(textpage=tp).split())
        spans = [s for block in source_page.get_text('dict',textpage=tp)['blocks']
                 for line in block.get('lines', []) for s in line['spans'] if s['text'].strip()]
        for a,b in bands:
            assert not any(s['bbox'][1] < b and s['bbox'][3] > a for s in spans), (a,b)
        small = [s for s in spans if s['size'] < 7.49]
        assert len(small) == 10 and all(s['font'] == 'ArialMT' for s in small)
        changes={id(s):(s,s['text']) for s in small}
        reference_changes={}
        if ijdrs:
            reference_changes={'strategies in Figure 5':'strategies in Figure 4',
                'See Figure 8 for class key':'See Supplementary Fig. S3 for class key'}
            for old,new in reference_changes.items():
                matches=[s for s in spans if old in unicodedata.normalize('NFKC',s['text'])]
                assert len(matches)==1
                s=matches[0]
                changes[id(s)]=(s,unicodedata.normalize('NFKC',s['text']).replace(old,new))
        expected_words=words_before.copy()
        for s,new in changes.values():
            expected_words.subtract(s['text'].split());expected_words.update(new.split())
        redaction_key=sha(json.dumps(dict(source=sha(source.read_bytes()),
            boxes=[list(s['bbox']) for s,new in changes.values()],
            method='MuPDF text-only redaction; images=0, graphics=0'),sort_keys=True).encode())
        cache_pdf=DEST/'tmp'/('redacted_'+redaction_key+'.pdf')
        cache_qa=cache_pdf.with_suffix('.json')
        reused_redaction=False
        if cache_pdf.exists() and cache_qa.exists() and json.loads(cache_qa.read_text())['sha256']==sha(cache_pdf.read_bytes()):
            src=fitz.open(cache_pdf)
            source_page=src[0]
            reused_redaction=True
        else:
            for s,new in changes.values():
                source_page.add_redact_annot(fitz.Rect(s['bbox']), fill=(1,1,1), cross_out=False)
            source_page.apply_redactions(images=0, graphics=0)
            cache_pdf.parent.mkdir(parents=True,exist_ok=True)
            src.save(cache_pdf,garbage=4,deflate=True,no_new_id=True)
            dump(cache_qa,dict(source_sha256=sha(source.read_bytes()),redaction_key=redaction_key,sha256=sha(cache_pdf.read_bytes())))
        font_buffer = font_program(src,'ArialMT')
        assert font_buffer
        # Insert the replacement labels on a small overlay. Inserting them
        # directly on the GIS page repeatedly scans its deeply nested fonts.
        overlay=fitz.open()
        text_page=overlay.new_page(width=source_page.rect.width,height=source_page.rect.height)
        insert_publication_font(text_page,'CompactArial',font_buffer,
            ''.join(new for s,new in changes.values()))
        for s,new in changes.values():
            center = (s['bbox'][0]+s['bbox'][2])/2
            width = fitz.Font(fontbuffer=font_buffer).text_length(new, fontsize=7.5)
            rgb = tuple(((s['color'] >> shift) & 255)/255 for shift in [16,8,0])
            text_page.insert_text((center-width/2, s['origin'][1]), new,
                              fontsize=7.5, fontname='CompactArial', color=rgb)
        place_vector(source_page,source_page.rect,overlay)
        tp=source_page.get_textpage(flags=fitz.TEXTFLAGS_DICT)
        actual_words=Counter(source_page.get_text(textpage=tp).split())
        if actual_words != +expected_words:
            diagnostics=dict(missing=dict(+expected_words-actual_words),extra=dict(actual_words-(+expected_words)))
            dump(DEST/'tmp/compact_text_diagnostic.json',diagnostics)
            src.save(DEST/'tmp/compact_text_diagnostic.pdf',garbage=4,deflate=True,no_new_id=True)
            raise AssertionError(diagnostics)
        updated_spans=[s for block in source_page.get_text('dict',textpage=tp)['blocks']
            for line in block.get('lines',[]) for s in line['spans'] if s['text'].strip()]
        min_font=min(s['size'] for s in updated_spans)
        assert min_font>=7.49
        print('Compact source labels checked; assembling unscaled strips',flush=True)
        width, height = src[0].rect.width, src[0].rect.height
        out = fitz.open()
        page = out.new_page(width=width, height=height-sum(b-a for a,b in bands))
        sections, top, target = [], 0., 0.
        for a,b in bands + [(height,height)]:
            if a > top:
                clip = fitz.Rect(0,top,width,a)
                box = fitz.Rect(0,target,width,target+clip.height)
                sections.append(dict(source_y=[top,a], target_y=[target,target+clip.height], scale=1.0))
                target += clip.height
            top = b
        pruned_bytes,pruning_qa,source_media=strip_source_document(
            src.tobytes(garbage=4,deflate=True,no_new_id=True),sections)
        print('Conservative strip pruning:',pruning_qa,flush=True)
        with fitz.open(stream=pruned_bytes,filetype='pdf') as strips:
            for i,section in enumerate(sections):
                a,b=section['source_y'];c,d=section['target_y']
                placement=place_vector(page,fitz.Rect(0,c,width,d),strips,
                    clip=fitz.Rect(0,a,width,b),pno=i)
                section['resource_name']=placement['resource_name']
        output.parent.mkdir(parents=True, exist_ok=True)
        out.set_metadata({'title':'Research workflow - compact layout variant', 'creator':'LA Grid publication artwork export'})
        out.save(output, garbage=4, deflate=True, no_new_id=True)
        canonicalize_strip_transforms(output,sections,source_media)
        # Validate the retained strips against the same source with only the
        # approved ten typography changes, allowing one clipping-edge pixel.
        with fitz.open(output) as final:
            f = np.array(render_image(final[0], 600))
            typography_mask=np.zeros(image.shape[:2],dtype=bool)
            ref_image=Image.fromarray(image,'RGB')
            high=np.asarray(ref_image.filter(ImageFilter.MaxFilter(3)),dtype=np.int16)
            low=np.asarray(ref_image.filter(ImageFilter.MinFilter(3)),dtype=np.int16)
            edge_support=np.max(high-low,axis=2)>0
            del high,low
            typography_regions=[]
            metrics=fitz.Font(fontbuffer=font_buffer)
            for s,new in changes.values():
                center=(s['bbox'][0]+s['bbox'][2])/2
                half=metrics.text_length(new,fontsize=7.5)/2
                box=fitz.Rect(center-half,s['origin'][1]-metrics.ascender*7.5,
                    center+half,s['origin'][1]-metrics.descender*7.5) | fitz.Rect(s['bbox'])
                box+=(-1,-1,1,1)
                typography_regions.append(list(box))
                x0,y0,x1,y1=[round(v*600/72) for v in box]
                typography_mask[max(0,y0):y1,max(0,x0):x1]=True
            strip_checks=[]
            total_pixels=total_changed=total_channel_difference=off_edge=maximum=0
            for section in sections:
                sy = [round(v*600/72) for v in section['source_y']]
                ty = [round(v*600/72) for v in section['target_y']]
                n = min(sy[1]-sy[0], ty[1]-ty[0])
                difference=abs(image[sy[0]+1:sy[0]+n-1].astype(np.int16)-f[ty[0]+1:ty[0]+n-1].astype(np.int16))
                delta=np.any(difference,axis=2)
                outside=delta & ~typography_mask[sy[0]+1:sy[0]+n-1]
                channel_max=np.max(difference,axis=2)
                significant_off_edge=outside & (channel_max>1) & ~edge_support[sy[0]+1:sy[0]+n-1]
                local_max=int(channel_max[outside].max()) if outside.any() else 0
                total_pixels+=outside.size
                total_changed+=int(outside.sum())
                total_channel_difference+=int(difference[outside].sum())
                off_edge+=int(significant_off_edge.sum())
                maximum=max(maximum,local_max)
                strip_checks.append(dict(source_y_px=sy,target_y_px=ty,
                    altered_pixels_inside_authorized_typography=int((delta & ~outside).sum()),
                    altered_pixels_outside_authorized_typography=int(outside.sum()),
                    max_channel_delta_outside_typography=local_max,
                    significant_changed_pixels_outside_original_edge_neighborhood=int(significant_off_edge.sum())))
            pixel_check=dict(compared_pixels=total_pixels,changed_pixels=total_changed,
                changed_fraction=total_changed/total_pixels,max_channel_delta=maximum,
                mean_absolute_rgb_delta=total_channel_difference/(total_pixels*3),
                significant_off_edge_changes=off_edge,all_nontypographic_pixels_exact=total_changed==0,
                rule='Exact unit vector translations; raster differences limited to a one-pixel neighborhood of existing edges, or <=1/255 quantization. Maximum channel difference <=32/255, changed fraction <=0.001 and mean absolute RGB difference <=0.005/255. Typography and one seam pixel excluded.')
            dump(DEST/'tmp/compact_pixel_check.json',pixel_check)
            assert off_edge==0 and maximum<=32 and pixel_check['changed_fraction']<=.001 and pixel_check['mean_absolute_rgb_delta']<=.005,pixel_check
            Image.fromarray(f,'RGB').save(output.with_suffix('.png'), dpi=(600,600))
            qa = dict(source=relative(source), source_sha256=sha(source.read_bytes()), output=relative(output),
                exporter_sha256=code_sha,png_sha256=sha(output.with_suffix('.png').read_bytes()),
                output_sha256=sha(output.read_bytes()), original_mm=[width*25.4/72,height*25.4/72],
                compact_mm=[page.rect.width*25.4/72,page.rect.height*25.4/72],
                removed_bands_pt=bands, sections=sections, source_text_inventory_preserved_except_reference_changes=True,
                reference_changes=reference_changes,
                geometry_preserved_with_bounded_edge_antialiasing=True,
                authorized_typography_rectangles_pt=typography_regions,
                direct_reference_png_sha256=sha(source.with_suffix('.png').read_bytes()),
                comparison='Final translated strips directly against the accepted SHA-bound 600-dpi PNG. Typography and one clipping-edge pixel excluded; finite-precision edge antialiasing is quantified, not falsely called pixel identity.',
                pixel_comparison=pixel_check,
                strip_pixel_checks=strip_checks,excluded_seam_pixels_per_edge=1,
                text_raised_from_7_to_7_5pt=[s['text'] for s in small], minimum_text_pt=min_font,
                minimum_text_basis='Directly measured on the modified source; every retained strip has a unit-scale transform and verified 600-dpi pixels. Avoids repeatedly expanding the same nested GIS page for text extraction.',
                reused_embedded_arial_sha256=sha(font_buffer),
                off_strip_form_pruning=pruning_qa,
                exact_decimal_unit_translations=True,
                no_plot_map_or_schedule_scaled=True)
        if reused_redaction:
            src.close()
    dump(qa_path, qa)
    print('Compact layout:', qa['compact_mm'], flush=True)
    return output


def validation_signature():
    functions=[equivalent,drawing_streams,unicode_maps,font_programs]
    text=''.join(inspect.getsource(f) for f in functions)
    text+=json.dumps({n:importlib.metadata.version(n) for n in ['PyMuPDF','pikepdf','Pillow']},sort_keys=True)
    return sha(text.encode())


def build_masters():
    audit_path = DEST/'qa/OBJECT_PREFLIGHT.json'
    if not audit_path.exists():
        audit()
    records = json.loads(audit_path.read_text())['figures']
    code_sha=sha(Path(__file__).read_bytes())
    validator_sha=validation_signature()
    progress_path=DEST/'tmp/optimization_progress.json'
    prior={}
    for candidate in [DEST/'universal/MASTERS.json',progress_path]:
        if candidate.exists():
            data=json.loads(candidate.read_text())
            for r in data['figures']:
                prior[r['identity']]=(r,data.get('exporter_sha256'))
    masters = []
    for (stem,key), record in zip(ITEMS, records):
        assert stem == record['figure']
        source = original(stem)
        assert sha(source.read_bytes()) == record['sha256']
        if key in prior:
            row,previous_validator=prior[key]
            if (row['source_sha256']==record['sha256'] and (ROOT/row['pdf']).exists()
                    and sha((ROOT/row['pdf']).read_bytes())==row['pdf_sha256']
                    and sha(source.with_suffix('.png').read_bytes())==row['png_sha256']):
                if row.get('validator_sha256')!=validator_sha:
                    row['verification']=equivalent(source,ROOT/row['pdf'])
                    row['validated_exporter_sha256']=code_sha
                    row['validator_sha256']=validator_sha
                masters.append(row)
                dump(progress_path,dict(exporter_sha256=code_sha,figures=masters))
                print(stem,'reuse verified delivery PDF',flush=True)
                continue
        output = DEST/'universal/optimized'/(key+'.pdf')
        result = optimize(source, output)
        try:
            checks = equivalent(source, output)
        except AssertionError as exc:
            failure = str(exc)
            result = optimize(source, output, subset=False)
            result['font_subset_candidate_rejected'] = failure
            checks = equivalent(source, output)
        saved = result['before_bytes']-result['after_bytes']
        keep = saved/result['before_bytes'] >= .01 and saved >= 65536
        if not keep:
            output.unlink()
        row = dict(identity=key, master_number=stem, accepted_source=relative(source),
            source_sha256=record['sha256'], pdf=relative(output if keep else source),
            pdf_sha256=sha((output if keep else source).read_bytes()),
            png=relative(source.with_suffix('.png')), png_sha256=sha(source.with_suffix('.png').read_bytes()),
            optimization=result, verification=checks, optimized_copy_retained=keep,
            width_mm=record['width_mm'], height_mm=record['height_mm'], min_text_pt=record['min_font_pt'],
            validator_sha256=validator_sha)
        masters.append(row)
        dump(progress_path,dict(exporter_sha256=code_sha,figures=masters))
        print(stem, 'lossless', round(result['after_bytes']/1048576,3), 'MiB', flush=True)
    dump(DEST/'universal/MASTERS.json',dict(baseline=BASE, exporter_sha256=code_sha,figures=masters,
        source_numerical_provenance=relative(SOURCE/'QA/SOURCE_IDENTITIES.json'),
        source_numerical_provenance_sha256=sha((SOURCE/'QA/SOURCE_IDENTITIES.json').read_bytes()),
        selection_rule='Retain an optimized copy only when exact pixel/text/drawing checks pass and size falls by at least 1% and 64 KiB; otherwise reference the unchanged accepted source. This avoids redundant copies, not a publisher file-size rule.'))
    caps=caption_records()
    text='# Journal-neutral figure captions\n\n'+''.join('## '+title+'\n\n'+body+'\n\n' for title,body in caps.values())
    (DEST/'universal/CAPTIONS.md').write_text(text,encoding='utf-8',newline='\n')


def registry():
    return {r['identity']:r for r in json.loads((DEST/'universal/MASTERS.json').read_text())['figures']}


def figure_path(key, ijdrs=False):
    if ijdrs and key == 'workflow':
        return ijdrs_workflow()
    return ROOT/registry()[key]['pdf']


def ijdrs_workflow():
    output=DEST/'tmp/workflow_ijdrs_references.pdf'
    if not output.exists():
        compact(ijdrs=True)
    return output


def caption_records():
    from publication_caption_definitions import refine
    text=(SOURCE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    parts=re.split(r'^## ',text,flags=re.M)[1:]
    assert len(parts)==16
    result,changes=refine({key:part.strip().split('\n\n',1) for (_,key),part in zip(ITEMS,parts)})
    dump(DEST/'qa/CAPTION_DEFINITION_CHANGES.json',changes)
    return result


def number_map():
    return {registry()[key]['master_number']:(f'Figure {i}' if group=='Main' else f'Supplementary Figure S{i}')
            for group,keys in [('Main',PRIMARY),('Supplement',SUPPLEMENT)] for i,key in enumerate(keys,1)}


def rewrite_references(text):
    mapping=number_map()
    pattern=r'\b(Supplementary )?Figures?\s+(S?\d+)(?:[-\u2013](S?\d+))?'
    def convert(match):
        supp=bool(match[1]) or match[2].startswith('S')
        first=int(match[2].lstrip('S'))
        last=int((match[3] or match[2]).lstrip('S'))
        labels=[]
        for i in range(first,last+1):
            token=f'FigS{i:02d}' if supp else f'Fig{i:02d}'
            labels.append(mapping[token])
        groups=[]
        for category in ['Figure ','Supplementary Figure S']:
            nums=[int(label[len(category):]) for label in labels if label.startswith(category)]
            if not nums:continue
            if len(nums)==1:groups.append(category+str(nums[0]));continue
            prefix='Figures ' if category=='Figure ' else 'Supplementary Figures S'
            if nums==list(range(nums[0],nums[-1]+1)):
                groups.append(prefix+str(nums[0])+'-'+('S' if category!='Figure ' else '')+str(nums[-1]))
            else:
                groups.append(prefix+(' and '.join(str(n) for n in nums)))
        return ' and '.join(groups)
    result=re.sub(pattern,convert,text)
    return re.sub(r'Supplementary Figure S(\d+) and Supplementary Figure S(\d+)',
                  r'Supplementary Figures S\1 and S\2',result)


def packet(keys, output, ijdrs=False):
    records=caption_records()
    out=fitz.open()
    with fitz.open(original('Fig01')) as font_source:
        arial=font_program(font_source,'ArialMT')
        bold=font_program(font_source,'Arial-BoldMT')
    metrics=fitz.Font(fontbuffer=arial)
    caption_characters=''.join(title+body for title,body in records.values())
    rows=[]
    for i,key in enumerate(keys,1):
        source=figure_path(key,ijdrs=ijdrs)
        title,body=records[key]
        if ijdrs:
            prefix=number_map()[registry()[key]['master_number']]
            title=prefix+'. '+title.split('. ',1)[1]
            body=rewrite_references(body)
        with fitz.open(source) as art:
            available=art[0].rect.width-32
            lines=0
            for para in (title+'\n\n'+body).split('\n'):
                line='';lines+=1
                for word in para.split():
                    candidate=(line+' '+word).strip()
                    if metrics.text_length(candidate,fontsize=9)>available:
                        lines+=1;line=word
                    else:line=candidate
            caption_height=lines*12+20
            page=out.new_page(width=art[0].rect.width,height=art[0].rect.height+caption_height+24)
            place_vector(page,art[0].rect,art)
            insert_publication_font(page,'CaptionArial',arial,caption_characters)
            insert_publication_font(page,'CaptionBold',bold,caption_characters)
            box=fitz.Rect(16,art[0].rect.height+12,page.rect.width-16,page.rect.height-12)
            page.insert_text((16,box.y0+9),title,fontname='CaptionBold',fontsize=9,color=(.12,.15,.17))
            box.y0+=22
            rest=page.insert_textbox(box,body,fontname='CaptionArial',fontsize=9,color=(.12,.15,.17))
            assert rest>=0,(key,rest)
            rows.append(dict(identity=key,page=i,source_pdf_sha256=sha(source.read_bytes()),caption_title=title))
    output.parent.mkdir(parents=True,exist_ok=True)
    out.set_metadata({'title':'IJDRS candidate artwork - not submission certified' if ijdrs else 'Universal scientific artwork',
                      'creator':'LA Grid journal-neutral export'})
    out.save(output,garbage=4,deflate=True,no_new_id=True)
    out.close()
    return rows


def prepare_configuration():
    records=caption_records()
    crosswalk=[]
    headings=['# IJDRS candidate captions','', 'Five main and eleven proposed supplementary figures. Supplementary acceptance remains unverified.','']
    for group,keys in [('Main',PRIMARY),('Supplement_Proposed',SUPPLEMENT)]:
        for i,key in enumerate(keys,1):
            row=registry()[key]
            label=number_map()[row['master_number']]
            crosswalk.append(dict(identity=key,master_number=row['master_number'],ijdrs_label=label,role=group,
                accepted_master=row['accepted_source'],master_sha256=row['source_sha256']))
            title,body=records[key]
            headings.extend(['## '+label+'. '+title.split('. ',1)[1],'',rewrite_references(body),''])
    (DEST/'IJDRS').mkdir(parents=True,exist_ok=True)
    (DEST/'IJDRS/CAPTIONS.md').write_text('\n'.join(headings),encoding='utf-8',newline='\n')
    dump(DEST/'IJDRS/FIGURE_REFERENCE_CROSSWALK.json',dict(baseline=BASE,figures=crosswalk))
    dump(DEST/'IJDRS/CONFIGURATION.json',dict(status='Author-review submission candidate; portal and ESM acceptance not certified',
        main=PRIMARY,supplementary_proposed=SUPPLEMENT,master_collection_preserved=True,
        workflow_layout='Scientifically equivalent compact variant; only cross-figure footer references are remapped for the candidate',
        main_limit_basis='Currently linked IJDRS Instructions for Authors; five figures and three tables without special editorial permission',
        supplementary_limit_verified=False,format='TIFF LZW, RGB, 600 dpi at native dimensions',
        original_manuscript_modified=False))
    pages={}
    pages['main']=packet(PRIMARY,DEST/'IJDRS/MAIN_WITH_CAPTIONS.pdf',ijdrs=True)
    pages['supplement']=packet(SUPPLEMENT,DEST/'IJDRS/SUPPLEMENT_PROPOSAL_WITH_CAPTIONS.pdf',ijdrs=True)
    dump(DEST/'qa/IJDRS_PACKET_REGISTRY.json',pages)


def review_previews():
    from colorspacious import cspace_convert
    tmp=DEST/'tmp/native_previews'
    tmp.mkdir(parents=True,exist_ok=True)
    gray_doc=fitz.open()
    review=[]
    for stem,key in ITEMS:
        path=figure_path(key)
        with fitz.open(path) as doc:
            im=render_image(doc[0],150)
            im.save(tmp/(stem+'.png'),dpi=(150,150))
            gray=im.convert('L').convert('RGB')
            p=gray_doc.new_page(width=doc[0].rect.width,height=doc[0].rect.height)
            buffer=io.BytesIO();gray.save(buffer,format='PNG')
            p.insert_image(p.rect,stream=buffer.getvalue())
            review.append(dict(identity=key,mode='grayscale',page=len(gray_doc)))
            if key in ['strategy_performance','community_context']:
                rgb=np.asarray(im,dtype=float)/255
                for kind in ['protanomaly','deuteranomaly','tritanomaly']:
                    cvd=np.clip(cspace_convert(rgb,{'name':'sRGB1+CVD','cvd_type':kind,'severity':100},'sRGB1'),0,1)
                    simulated=Image.fromarray(np.rint(cvd*255).astype(np.uint8),'RGB')
                    p=gray_doc.new_page(width=doc[0].rect.width,height=doc[0].rect.height)
                    buffer=io.BytesIO();simulated.save(buffer,format='PNG')
                    p.insert_image(p.rect,stream=buffer.getvalue())
                    review.append(dict(identity=key,mode=kind,page=len(gray_doc),severity=100))
    gray_doc.save(DEST/'qa/ACCESSIBILITY_REVIEW.pdf',garbage=4,deflate=True,no_new_id=True)
    dump(DEST/'qa/ACCESSIBILITY_PAGE_REGISTRY.json',dict(pages=review,
        method='Grayscale via Pillow luminance; Machado-model severity-100 CVD simulation via colorspacious. A simulation is not certification of universal accessibility.'))
    comparison=fitz.open()
    for path in [original('Fig01'),DEST/'universal/layout_variants/workflow_compact.pdf']:
        with fitz.open(path) as doc:
            im=render_image(doc[0],150)
            im.save(tmp/(path.stem+'_comparison.png'))
            p=comparison.new_page(width=doc[0].rect.width,height=doc[0].rect.height)
            data=io.BytesIO();im.save(data,format='PNG');p.insert_image(p.rect,stream=data.getvalue())
    comparison.save(DEST/'qa/WORKFLOW_NATIVE_SIZE_COMPARISON.pdf',garbage=4,deflate=True,no_new_id=True)
    with fitz.open(DEST/'universal/layout_variants/workflow_compact.pdf') as doc:
        im=render_image(doc[0],150)
        im.save(tmp/'workflow_compact_native.png',dpi=(150,150))
        # 174 and 85 mm are illustrative placement tests, not IJDRS mandates.
        for width in [174,85]:
            ratio=width/(doc[0].rect.width*25.4/72)
            preview=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)
            preview.save(tmp/f'workflow_at_{width}mm.png',dpi=(150,150))


def svg_example():
    path=figure_path('strategy_performance')
    out=DEST/'universal/vector_example/strategy_performance.svg'
    out.parent.mkdir(parents=True,exist_ok=True)
    with fitz.open(path) as doc:
        assert not doc[0].get_images()
        svg=doc[0].get_svg_image(text_as_path=True)
        assert '<image' not in svg
        (DEST/'tmp/strategy_performance_svg_trial.svg').write_text(svg,encoding='utf-8',newline='\n')
        with fitz.open(stream=svg.encode(),filetype='svg') as vector:
            converted=vector.convert_to_pdf()
        with fitz.open(stream=converted,filetype='pdf') as check:
            a=np.array(render_image(doc[0],600),dtype=float)
            b=np.array(render_image(check[0],600),dtype=float)
            assert a.shape==b.shape
            delta=abs(a-b)
            mean=float(delta.mean());large=float(np.mean(np.max(delta,axis=2)>20))
            approved=mean<=1 and large<=.005
            preview=DEST/'tmp/native_previews/SVG_example.png'
            preview.parent.mkdir(parents=True,exist_ok=True)
            render_image(check[0],150).save(preview)
    if approved:
        out.write_text(svg,encoding='utf-8',newline='\n')
    elif out.exists():
        out.unlink()
    dump(DEST/'qa/SVG_EXAMPLE_QA.json',dict(source=relative(path),source_sha256=sha(path.read_bytes()),
        approved_for_production=approved,
        status='APPROVED' if approved else 'REJECTED: appearance round-trip exceeds declared limits',
        svg=relative(out) if approved else None,sha256=sha(out.read_bytes()) if approved else None,
        trial_sha256=sha(svg.encode()),raster_objects=0,
        mean_absolute_rgb_delta_600dpi=mean,fraction_pixels_delta_gt20=large,
        text_is_outlined=True,fully_editable_text=False,
        note='Optional SVG requires mean RGB difference <=1 and fraction of pixels differing by >20 <=0.005 at 600 dpi. Failed trials remain untracked and are not offered as production artwork. Original vector PDF/code remain authoritative.'))


def export_raster(pdf, output, dpi=600, width_mm=None, fmt='tiff', allow_small=False):
    output=output.resolve()
    if output==pdf.resolve() or output.is_relative_to(SOURCE.resolve()):
        raise ValueError('Accepted master paths are read-only to this exporter.')
    valid_suffixes={'tiff':{'.tif','.tiff'},'png':{'.png'}}
    if fmt not in valid_suffixes or output.suffix.lower() not in valid_suffixes[fmt]:
        raise ValueError('The filename extension must match the actual export format.')
    if dpi<=0 or (width_mm is not None and width_mm<=0):
        raise ValueError('Positive physical width and resolution are required.')
    with fitz.open(pdf) as doc:
        native_width = doc[0].rect.width*25.4/72
        scale = width_mm/native_width if width_mm is not None else 1.
        known={str(ROOT/r['pdf']):r['min_text_pt'] for r in registry().values()} if (DEST/'universal/MASTERS.json').exists() else {}
        if pdf.name in ['workflow_compact.pdf','workflow_ijdrs_references.pdf']:
            min_pt=json.loads((DEST/'qa/COMPACT_LAYOUT_QA.json').read_text())['minimum_text_pt']*scale
        elif str(pdf) in known:
            min_pt=known[str(pdf)]*scale
        else:
            spans = [s for b in doc[0].get_text('dict')['blocks'] for line in b.get('lines', [])
                     for s in line['spans'] if s['text'].strip()]
            min_pt=min(s['size'] for s in spans)*scale
        if min_pt < 6.99 and not allow_small:
            raise ValueError(f'Placement would reduce text to {min_pt:.2f} pt. Reflow or explicitly approve smaller lettering; do not silently shrink.')
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(dpi/72*scale,dpi/72*scale), alpha=False)
        im = Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
    output.parent.mkdir(parents=True, exist_ok=True)
    profile_path=DEST/'universal/color/srgb.icc'
    if not profile_path.exists():
        profile_path.parent.mkdir(parents=True,exist_ok=True)
        profile_path.write_bytes(ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
    profile=profile_path.read_bytes()
    if fmt == 'tiff':
        im.save(output, format='TIFF', compression='tiff_lzw', dpi=(dpi,dpi), icc_profile=profile)
    elif fmt == 'png':
        im.save(output, format='PNG', dpi=(dpi,dpi), icc_profile=profile)
    else:
        raise ValueError(fmt)
    with Image.open(output) as back:
        assert back.mode == 'RGB' and back.size == im.size
        assert np.array_equal(np.asarray(back),np.asarray(im))
        assert abs(back.info['dpi'][0]-dpi) < .1 and back.info.get('icc_profile')
    return dict(source=relative(pdf), source_sha256=sha(pdf.read_bytes()), output=relative(output),
        sha256=sha(output.read_bytes()), bytes=output.stat().st_size, pixels=list(im.size), dpi=dpi,
        rendered_rgb_sha256=sha(im.tobytes()),
        size_mm=[n/dpi*25.4 for n in im.size], min_printed_text_pt=min_pt,
        roundtrip_rgb_pixels_identical=True, color='8-bit RGB; sRGB output interpretation; no CMYK conversion',
        icc_sha256=sha(profile),
        compression='LZW lossless' if fmt == 'tiff' else 'PNG lossless')


def exports():
    rows = []
    for group, keys in [('Main',PRIMARY),('Supplement_Proposed',SUPPLEMENT)]:
        for i,key in enumerate(keys,1):
            name = f'Fig{i:02d}' if group == 'Main' else f'FigS{i:02d}'
            output = DEST/'IJDRS'/group/(name+'_'+key+'.tif')
            row = export_raster(figure_path(key,ijdrs=True),output)
            if key=='workflow':
                row['transient_render_pdf_sha256']=row['source_sha256']
                row['source']=relative(DEST/'universal/layout_variants/workflow_compact.pdf')
                row['source_sha256']=sha((ROOT/row['source']).read_bytes())
                row['render_recipe']='Compact workflow + two cross-reference text substitutions documented in qa/IJDRS_WORKFLOW_REFERENCE_QA.json'
            row.update(identity=key, ijdrs_number=name, role=group)
            rows.append(row)
            print('TIFF600',name,key,flush=True)
    dump(DEST/'IJDRS/EXPORT_MANIFEST.json',dict(profile='IJDRS candidate - not portal certified',figures=rows,
        note='Five main and eleven proposed supplementary artworks, not an assertion that IJDRS permits eleven supplemental figures. Universal source numbering is unchanged.'))


def summarize():
    entries=registry()
    technical=json.loads((DEST/'qa/OBJECT_PREFLIGHT.json').read_text())['figures']
    rows=['# Complete artwork preflight','',
        'Original numbered masters are preserved. Sizes are MiB; dimensions are native millimeters. TIFFs are separate 600-dpi lossless RGB derivatives. Technical readiness is not journal acceptance.','',
        '| Master / stable identity | Dimensions | Original / delivery PDF MiB | Type | Formats | Action |',
        '|---|---|---|---|---|---|']
    for (stem,key),obj in zip(ITEMS,technical):
        item=entries[key]
        size=(ROOT/item['pdf']).stat().st_size/1048576
        kind='Vector + raster resources' if obj['images'] else 'Vector'
        action='Preserve native size; do not blindly reduce lettering.' if obj['min_font_pt']<7.99 else 'Confirm final placement.'
        if key=='workflow':action='Compact variant supplied; GIS forms dominate bytes.'
        if key=='community_context':action='Bivariate grayscale loses a dimension; companion retained.'
        if key=='mapping_gate_sensitivity':action='Approved 185 x 145 mm original unchanged.'
        svg_ok=json.loads((DEST/'qa/SVG_EXAMPLE_QA.json').read_text())['approved_for_production']
        formats='PDF, PNG600, TIFF600'+(', outlined SVG' if key=='strategy_performance' and svg_ok else '')
        rows.append(f"| {stem} / `{key}` | {obj['width_mm']:.1f} x {obj['height_mm']:.1f} | {obj['bytes']/1048576:.2f} / {size:.2f} | {kind} | {formats} | {action} |")
    f=technical[0];best=entries['workflow']
    compact_qa=json.loads((DEST/'qa/COMPACT_LAYOUT_QA.json').read_text())
    rows.extend(['','## Figure 1','',
        f"Original: {f['bytes']:,} bytes ({f['bytes']/1048576:.2f} MiB), 185 x {f['height_mm']:.3f} mm. Exact-appearance delivery PDF: {(ROOT/best['pdf']).stat().st_size:,} bytes.",
        f"Stored form streams: {f['stream_bytes']['form']:,} bytes ({100*f['stream_bytes']['form']/f['bytes']:.2f}% of file); images: {f['stream_bytes']['image']:,} bytes. Raw duplicate-stream upper bound: {f['potential_raw_duplicate_bytes']:,} bytes. Full-page GIS imports remain invoked under clipping; generic resource pruning cannot simply delete that painted geometry.",
        'No image recompression, map simplification or page rasterization is used for the optimized PDF. Drawing streams, text operators/Unicode maps and 150/600-dpi appearance are checked against the accepted source and its SHA-bound PNG.',
        f"Compact layout: {compact_qa['compact_mm'][0]:.2f} x {compact_qa['compact_mm'][1]:.2f} mm. All maps, schedules and event values stay unscaled; minimum text is {compact_qa['minimum_text_pt']:.2f} pt. The full-height original remains available.",
        'At 174-mm placement, 7.5-pt lettering becomes about 7.05 pt; at 85 mm, about 3.45 pt. Single-column reduction is unsuitable without reflow. These are placement tests, not IJDRS column mandates.',
        '', '## Limits','',
        'Native masters contain 7-7.5-pt details, below the usual 8-12-pt preference in general Springer artwork examples. They are not certified for arbitrary reduction. Thin GIS lines, overlapping strategy curves and hue-dependent classes require color/vector viewing or an accessible alternative.',
        'PDF image-DPI ranges include invoked resources under clipping, not necessarily visible images. Tiny gradient resources do not cause the large workflow file. Journal-specific gates are in JOURNAL_COMPLIANCE.md; no 10-MB acceptance cutoff is imposed.'])
    (DEST/'PREFLIGHT_SUMMARY.md').write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
    dump(DEST/'qa/ENVIRONMENT.json',dict(python=sys.version,base=BASE,
        versions={name:importlib.metadata.version(name) for name in ['PyMuPDF','pikepdf','Pillow','numpy','colorspacious']},
        exporter_sha256=sha(Path(__file__).read_bytes())))


def build_fingerprint():
    assets={relative(p):sha(p.read_bytes()) for pdf in source_files() for p in [pdf,pdf.with_suffix('.png')]}
    assets['captions_normalized']=sha((SOURCE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8').encode())
    assets['exporter']=sha(Path(__file__).read_bytes())
    assets['caption_definitions']=sha((Path(__file__).parent/'publication_caption_definitions.py').read_bytes())
    profile=DEST/'universal/color/srgb.icc'
    assets['frozen_srgb_icc']=sha(profile.read_bytes()) if profile.exists() else None
    assets['versions']={n:importlib.metadata.version(n) for n in ['PyMuPDF','pikepdf','Pillow','numpy','colorspacious']}
    return sha(json.dumps(assets,sort_keys=True).encode())


def build(force=False):
    cache_path=DEST/'qa/BUILD_CACHE.json'
    if cache_path.exists() and not force:
        cached=json.loads(cache_path.read_text())
        if cached['fingerprint']==build_fingerprint() and all((ROOT/p).exists() and sha((ROOT/p).read_bytes())==h for p,h in cached['outputs'].items()):
            print('Reused verified export graph; source and output hashes match. No artwork rewritten.',flush=True)
            return
    build_masters();compact();prepare_configuration();exports();review_previews();svg_example();summarize()
    suffixes={'.pdf','.png','.tif','.icc','.svg'}
    names={'MASTERS.json','CAPTIONS.md','EXPORT_MANIFEST.json','CONFIGURATION.json','FIGURE_REFERENCE_CROSSWALK.json','PREFLIGHT_SUMMARY.md'}
    outputs={relative(p):sha(p.read_bytes()) for p in DEST.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(DEST).parts
             and p!=cache_path and (p.suffix.lower() in suffixes or p.name in names or p.parent==DEST/'qa')}
    dump(cache_path,dict(fingerprint=build_fingerprint(),outputs=outputs,
        note='Hash-validated reuse avoids rewriting/uploading identical derivatives. --force bypasses this whole-graph cache; individually verified master optimization rows may still be reused.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['audit', 'trial', 'masters', 'compact', 'exports', 'configuration','review','svg','build','export'])
    parser.add_argument('--identity',choices=[key for _,key in ITEMS])
    parser.add_argument('--format',choices=['tiff','png'],default='tiff')
    parser.add_argument('--dpi',type=int,choices=[300,600,1200],default=600)
    parser.add_argument('--width-mm',type=float)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--force',action='store_true')
    args = parser.parse_args()
    if args.operation == 'audit':
        audit()
    elif args.operation == 'masters':
        build_masters()
    elif args.operation == 'compact':
        compact()
    elif args.operation == 'exports':
        exports()
    elif args.operation == 'configuration':
        prepare_configuration()
    elif args.operation == 'review':
        review_previews()
    elif args.operation == 'svg':
        svg_example()
    elif args.operation == 'build':
        build(force=args.force)
    elif args.operation == 'export':
        if not args.identity or not args.output:
            parser.error('export requires --identity and --output')
        print(json.dumps(export_raster(figure_path(args.identity),args.output.resolve(),
                                      args.dpi,args.width_mm,args.format),indent=2))
    else:
        out = DEST/'tmp/workflow_fontsubset.pdf'
        print(json.dumps(optimize(SOURCE/'Main/Fig01.pdf', out), indent=2))


if __name__ == '__main__':
    main()
