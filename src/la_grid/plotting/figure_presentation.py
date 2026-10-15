"""Presentation-only changes to existing vector artwork, without redrawing data."""
import hashlib
import io
import json
import re
from pathlib import Path
from collections import Counter

import fitz

_HEADING_OFFSETS={}


def spans(page):
    return [s for b in page.get_text('dict')['blocks'] for line in b.get('lines', []) for s in line['spans']]


def vector_signature(page):
    drawings=[{k:repr(v) for k,v in d.items() if k not in ['seqno','layer']} for d in page.get_drawings()]
    return hashlib.sha256(json.dumps(drawings,sort_keys=True).encode()).hexdigest()


def fonts(doc, bold, required):
    candidates=[]
    for row in doc[0].get_fonts():
        if ('Bold' in row[3])!=bold:
            continue
        raw=doc.extract_font(row[0])[3]
        if not raw:
            continue
        font=fitz.Font(fontbuffer=raw)
        if all(font.has_glyph(ord(c)) for c in required if not c.isspace()):
            candidates.append((hashlib.sha256(raw).hexdigest(),raw,font))
    if not candidates:
        path=Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf')
        raw=path.read_bytes()
        font=fitz.Font(fontbuffer=raw)
        assert all(font.has_glyph(ord(c)) for c in required if not c.isspace())
        return raw,font
    return sorted(candidates,key=lambda v:v[0])[0][1:]


def remove(page, selected):
    before=vector_signature(page)
    key=lambda s:(s['text'].replace('\u00a0',' '),tuple(round(x,3) for x in s['origin']))
    excluded={key(s) for s in selected}
    expected=[s for s in spans(page) if key(s) not in excluded]
    expected_keys=Counter(key(s) for s in expected)
    for s in selected:
        page.add_redact_annot(fitz.Rect(s['bbox'])+(-.03,-.03,.03,.03),fill=None)
    page.apply_redactions(images=0,graphics=0)
    # Compound source PDFs can share text runs across clipping forms. Restore
    # any untouched legend displaced by redaction at its exact original origin.
    extra=Counter(key(s) for s in spans(page))-expected_keys
    for s in spans(page):
        if extra[key(s)]:
            page.add_redact_annot(fitz.Rect(s['bbox']),fill=None)
            extra[key(s)]-=1
    if sum(extra.values())==0:
        page.apply_redactions(images=0,graphics=0)
    actual=Counter(key(s) for s in spans(page))
    for s in expected:
        k=key(s)
        if actual[k]:
            actual[k]-=1
            continue
        bold='Bold' in s['font'];name='RestoredBold' if bold else 'RestoredBody'
        path=Path('C:/Windows/Fonts')/('arialbd.ttf' if bold else 'arial.ttf')
        page.insert_font(fontname=name,fontfile=str(path))
        page.insert_text(s['origin'],s['text'],fontname=name,fontsize=s['size'],
                         color=fitz.sRGB_to_pdf(s['color']))
    missing=expected_keys-Counter(key(s) for s in spans(page))
    assert not missing, ('An untouched label was lost',missing)
    assert vector_signature(page)==before, 'A text correction changed a scientific vector'
    return before


def title(page, text, x, top, font, center=False):
    # Use one complete, explicitly embedded face. Reusing a subset extracted
    # from nested historical forms can give CID-coded gibberish after grafting.
    raw=Path('C:/Windows/Fonts/arialbd.ttf').read_bytes()
    metrics=fitz.Font(fontbuffer=raw)
    page.insert_font(fontname='CurrentPanelHeading14',fontbuffer=raw)
    if center:
        if text not in _HEADING_OFFSETS:
            with fitz.open() as probe:
                p=probe.new_page(width=1000,height=40)
                p.insert_font(fontname='CurrentPanelHeading14',fontbuffer=raw)
                p.insert_text((10,20),text,fontname='CurrentPanelHeading14',fontsize=9.5)
                boxes=[s['bbox'] for s in spans(p)]
                _HEADING_OFFSETS[text]=(min(b[0] for b in boxes)+max(b[2] for b in boxes))/2-10
        x-=_HEADING_OFFSETS[text]
    page.insert_text((x,top+metrics.ascender*9.5),text,fontname='CurrentPanelHeading14',fontsize=9.5,color=(0,0,0))


def tile(page, doc, rect, dy=0):
    rect=fitz.Rect(rect)
    page.show_pdf_page(rect+(0,dy,0,dy),doc,0,clip=rect,keep_proportion=False)


def finish(doc):
    return doc.tobytes(garbage=4,deflate=True,no_new_id=True)


def figure5(raw):
    with fitz.open(stream=raw,filetype='pdf') as source:
        p=source[0];w,h=p.rect.width,p.rect.height
        old=[s for s in spans(p) if s['text'][:3] in [f'{c}. ' for c in 'ABCDE']
             or s['text'][:3] in [f'{c}.\u00a0' for c in 'ABCDE']]
        assert len(old)==5
        labels={s['text'][0]:s['text'].replace('\u00a0',' ').replace('\u00ad','-') for s in old}
        font=fonts(source,True,''.join(labels.values()))
        signature=remove(p,old)
        out=fitz.open();page=out.new_page(width=w,height=h)
        tile(page,source,(0,0,w,55),6)
        tile(page,source,(0,70,w,254),-8)
        tile(page,source,(0,281,w,451))
        tile(page,source,(0,484,w,502),8.5)
        tile(page,source,(0,511,w,h))
        positions={'A':64.,'B':64.,'C':268.1,'D':268.1,'E':471.0}
        for s in old:
            code=s['text'][0]
            title(page,labels[code],(s['bbox'][0]+s['bbox'][2])/2,positions[code],font,center=True)
        result=finish(out);out.close()
        return result,dict(scientific_vectors_unchanged=signature,
            translations_pt=dict(top_legend=6,AB=-8,CD=0,E_maps=0,E_legend=8.5),
            title_top_pt=positions,AB_to_CD_gap_pt=268.1-(252.1-8),CD_to_E_gap_pt=471.0-446.8752,
            font_pt=9.5,width_pt=w,height_pt=h)


def figure7(raw):
    with fitz.open(stream=raw,filetype='pdf') as source:
        p=source[0];w,h=p.rect.width,p.rect.height
        texts=spans(p)
        removed=[s for s in texts if s['text'].startswith((
            'A. Feature distributions','B. Seven-coordinate','C. Saved seven-variable',
            'D. Recovery burden','Exact empirical CDFs;','Ordinary feature z means,',
            '2,299 tracts;','P2 model IDs;','Finite five-policy comparison.',
            'Descriptive co-occurrence;','Frozen SOVI','Q4 and deficit >= frozen P75'))]
        assert len(removed)==12,len(removed)
        labels=['A. Feature distributions','B. Profiles','C. Community types',
                'D. Recovery burden and social vulnerability']
        font=fonts(source,True,''.join(labels))
        body,metrics=fonts(source,False,'SOVI quartileQ4 and deficit >= P75')
        signature=remove(p,removed)
        p.insert_font(fontname='MapLegend',fontbuffer=body)
        for original,new,rotation in [('Frozen SOVI','SOVI quartile',90),
                                      ('Q4 and deficit >= frozen P75','Q4 and deficit >= P75',0)]:
            s=next(s for s in removed if s['text']==original)
            p.insert_text(s['origin'],new,fontname='MapLegend',fontsize=7.5,rotate=rotation)
        out=fitz.open();page=out.new_page(width=w,height=h)
        tile(page,source,(0,30,w,265),-8)
        tile(page,source,(0,302,w,408),-14)
        tile(page,source,(0,416,w,641),7)
        positions=[(12.96,10.4),(12.96,276.5),(23.328,412.7),(277.344,412.7)]
        for text,(x,y) in zip(labels,positions):title(page,text,x,y,font)
        result=finish(out);out.close()
        return result,dict(scientific_vectors_unchanged=signature,
            translations_pt=dict(A=-8,B=-14,CD=7),titles=labels,
            A_to_B_gap_pt=276.5-(264.4724-8),B_to_CD_gap_pt=412.7-(406.6855-14),
            embedded_explanatory_notes_removed=6,font_pt=9.5,width_pt=w,height_pt=h,
            scientific_arrays_and_classification_reused=True)


def supplementary8(raw):
    replacements={
        'Thin curves: saved seeds 42-46':'Thin curves: seeds 42-46',
        'C  Saved partition agreement':'C  Partition agreement',
        'P2 seven-variable typology: saved selection and sensitivity evidence':'Clustering diagnostics',
        'Agreement comparisons are descriptive internal diagnostics, not independent physical validation.':'',
    }
    with fitz.open(stream=raw,filetype='pdf') as doc:
        p=doc[0];old=[s for s in spans(p) if s['text'] in replacements]
        assert len(old)==4,len(old)
        selected={}
        for bold in [False,True]:
            required=''.join(replacements[s['text']] for s in old if ('Bold' in s['font'])==bold)
            selected[bold]=fonts(doc,bold,required)
        signature=remove(p,old)
        for s in old:
            text=replacements[s['text']]
            if not text:continue
            bold='Bold' in s['font'];raw_font,metrics=selected[bold]
            name='CleanBold' if bold else 'CleanBody'
            p.insert_font(fontname=name,fontbuffer=raw_font)
            point=s['origin']
            if text=='Clustering diagnostics':
                point=((p.rect.width-metrics.text_length(text,fontsize=s['size']))/2,point[1])
            p.insert_text(point,text,fontname=name,fontsize=s['size'])
        return finish(doc),dict(scientific_vectors_unchanged=signature,text_only_replacements=replacements)


def apply(stem,raw):
    return {'Main/Fig05':figure5,'Main/Fig07':figure7,'Supplement/FigS08':supplementary8}[stem](raw)


def relabel(raw, replacements):
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        selected=[s for s in spans(page) if s['text'] in replacements]
        assert len(selected)==len(replacements),(len(selected),list(replacements))
        out=cut_text(doc,selected);page=out[0]
        for s in selected:
            text=replacements[s['text']]
            if not text:continue
            raw_font,metrics=fonts(doc,'Bold' in s['font'],text)
            page.insert_font(fontname='NewLabel'+str(selected.index(s)),fontbuffer=raw_font)
            x=(s['bbox'][0]+s['bbox'][2]-metrics.text_length(text,fontsize=s['size']))/2
            page.insert_text((x,s['origin'][1]),text,fontsize=s['size'],
                             fontname='NewLabel'+str(selected.index(s)))
        result=finish(out);out.close();return result


def cut_text(doc, selected):
    """Omit only label rectangles; leave the underlying vector streams intact."""
    rect=doc[0].rect
    holes=[fitz.Rect(s['bbox'])+(-.2,-.2,.2,.2) for s in selected]
    ys=sorted({0.,rect.height,*[max(0.,h.y0) for h in holes],*[min(rect.height,h.y1) for h in holes]})
    out=fitz.open();p=out.new_page(width=rect.width,height=rect.height)
    for lo,hi in zip(ys,ys[1:]):
        ranges=sorted((max(0.,h.x0),min(rect.width,h.x1)) for h in holes if h.y0<hi-1e-5 and h.y1>lo+1e-5)
        x=0.
        for left,right in ranges:
            if left>x:tile(p,doc,(x,lo,left,hi))
            x=max(x,right)
        if x<rect.width:tile(p,doc,(x,lo,rect.width,hi))
    return out


def recovery_network(raw):
    """Separate static removal from the two time-dependent recovery measures."""
    with fitz.open(stream=raw,filetype='pdf') as doc:
        p=doc[0];w=p.rect.width
        old=[s for s in spans(p) if re.match(r'^[ABC]\. ',s['text'])]
        assert len(old)==3
        names=['A. Static percolation','B. Recovery of largest-component fraction',
               'C. Recovery of mean degree in the largest component']
        font=fonts(doc,True,''.join(names));signature=vector_signature(p)
        out=fitz.open();page=out.new_page(width=w,height=642)
        tile(page,doc,(0,36,w,168),4)
        tile(page,doc,(0,210,w,354),13)
        tile(page,doc,(0,390,w,530),32.25)
        tile(page,doc,(0,540,w,610),32.25)
        header=Path('C:/Windows/Fonts/arialbd.ttf').read_bytes()
        metric=fitz.Font(fontbuffer=header)
        page.insert_font(fontname='RecoveryColumnHeading',fontbuffer=header)
        for label,x in [('Four focal policies',152.0),('Other selected policies',411.6)]:
            page.insert_text((x-metric.text_length(label,fontsize=7.5)/2,424+metric.ascender*7.5),
                             label,fontname='RecoveryColumnHeading',fontsize=7.5)
        for name,y in zip(names,[12,192,387]):title(page,name,w/2,y,font,center=True)
        result=finish(out);out.close()
        return result,dict(scientific_vector_signature=signature,
            translations_pt=dict(static=4,component_recovery=13,degree_recovery=32.25,legend=32.25),
            recovery_column_headers_repeated=True,
            title_top_pt=[12,192,387],preceding_content_to_title_gap_pt=[20,20])


def gate_sensitivity(raw, values):
    """Use saved means/ranges; combine both threshold tests on one common axis."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8.5,
        'xtick.labelsize':7.5,'ytick.labelsize':8,'pdf.fonttype':42,'ps.fonttype':42})
    names=['Impact-first','Hospital-first','Degree-first']
    keys=['impact-first','hospital-first','degree-first']
    records=[]
    fig=plt.figure(figsize=(185/25.4,210/25.4))
    height=210*72/25.4
    ax=fig.add_axes([.23,(height-340)/height,.70,108/height])
    tx=fig.add_axes([.23,(height-558)/height,.70,108/height])
    for i,(key,color,marker) in enumerate(zip(keys,['#d98200','#595959','#45a437'],['s','o','^'])):
        r=values.loc[values.policy.eq(key)&values.threshold.eq(.5)].iloc[0]
        ax.errorbar(r.mean_gap_h,2-i,xerr=[[r.mean_gap_h-r.p05_gap_h],[r.p95_gap_h-r.mean_gap_h]],
                    color=color,marker=marker,markersize=4,lw=1)
        records.append(r.to_dict())
    for threshold,color,marker,dy in [(.05,'#147f98','o',.14),(.75,'#7a5899','s',-.14)]:
        for i,key in enumerate(keys):
            r=values.loc[values.policy.eq(key)&values.threshold.eq(threshold)].iloc[0]
            tx.errorbar(r.mean_gap_h,2-i+dy,
                xerr=[[r.mean_gap_h-r.p05_gap_h],[r.p95_gap_h-r.mean_gap_h]],
                color=color,marker=marker,markersize=4,lw=1,
                label=f'Threshold {threshold:.2f}' if i==0 else None)
            records.append(r.to_dict())
    tx.legend(loc='lower left',bbox_to_anchor=(0,1.12),ncol=2,frameon=False,fontsize=8,
              borderaxespad=0,handletextpad=.4,columnspacing=1.8)
    for a in [ax,tx]:
        a.set_yticks([2,1,0],names);a.set_ylim(-.5,2.5)
        a.axvline(0,color='#777777',lw=.6,zorder=0)
        a.grid(axis='x',color='#dddddd',lw=.4);a.set_axisbelow(True)
        a.set_xlabel('Service-loss gap (h)')
        for side in ['top','right']:a.spines[side].set_visible(False)
        for side in ['bottom','left']:a.spines[side].set_color('#aaaaaa')
        a.tick_params(length=2,width=.5)
    ax.set_xlim(-7.3,.3);tx.set_xlim(-.17,.06)
    tx.set_xticks([-.15,-.10,-.05,0,.05])
    buf=io.BytesIO();fig.savefig(buf,format='pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
    with fitz.open(stream=raw,filetype='pdf') as source,fitz.open(stream=buf.getvalue(),filetype='pdf') as out:
        p=source[0];old=[s for s in spans(p) if s['text'].startswith('A. Effect')]
        assert len(old)==1
        page=out[0];w=page.rect.width
        clean_a=cut_text(source,[dict(old[0],bbox=(180,8,380,26))])
        tile(page,clean_a,(145,19,385,162),12);clean_a.close()
        names=['A. Mapping-weight cutoff','B. Removing source connectivity (threshold 0.50)',
               'C. Functionality threshold (reference 0.50)']
        font=fonts(source,True,''.join(names))
        for name,y in zip(names,[12,198,393]):title(page,name,w/2,y,font,center=True)
        # The clipped legacy A source carries unused Base-14 resources from
        # hidden historical panels. Embed compatible faces for PDF portability.
        visible={s['font'] for s in spans(page)}
        for row in page.get_fonts():
            if out.extract_font(row[0])[3]:continue
            assert row[3] in ['Helvetica','Helvetica-Bold'] and row[3] not in visible
            bold=row[3].endswith('Bold');name='Arial-BoldMT' if bold else 'ArialMT'
            data=Path('C:/Windows/Fonts', 'arialbd.ttf' if bold else 'arial.ttf').read_bytes()
            metric=fitz.Font(fontbuffer=data)
            stream=out.get_new_xref();out.update_object(stream,'<<>>');out.update_stream(stream,data)
            desc=out.get_new_xref()
            bbox=' '.join(str(round(v*1000)) for v in fitz.Rect(metric.bbox))
            out.update_object(desc,f'<< /Type /FontDescriptor /FontName /{name} /Flags 32 /FontBBox [{bbox}] '
                f'/ItalicAngle 0 /Ascent {round(metric.ascender*1000)} /Descent {round(metric.descender*1000)} '
                f'/CapHeight 716 /StemV 80 /FontFile2 {stream} 0 R >>')
            widths=' '.join(str(round(metric.text_length(bytes([i]).decode('cp1252',errors='replace'),fontsize=1000))) for i in range(256))
            out.update_object(row[0],f'<< /Type /Font /Subtype /TrueType /BaseFont /{name} '
                f'/FirstChar 0 /LastChar 255 /Widths [{widths}] /Encoding /WinAnsiEncoding /FontDescriptor {desc} 0 R >>')
        result=finish(out)
    return result,dict(saved_display_records=records,thresholds=[.05,.75],reference_threshold=.5,
        source_control_threshold=.5,source_control_separate=True,no_simulation_or_new_statistics=True)


def priority_geography(raw):
    """Change only the population-context fill/colorbar to ordered neutral gray."""
    from matplotlib import colormaps,colors
    import numpy as np
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        before=page.get_drawings()
        fills={d['fill'] for d in before if d['fill'] and d['rect'].y0>525 and
               d['fill'][2]-d['fill'][0]>.04 and d['fill'][2]>d['fill'][1]}
        samples=colormaps['Blues'](np.linspace(0,1,256))[:,:3]
        fills={rgb for rgb in fills if np.min(np.linalg.norm(samples-np.array(rgb),axis=1))<2e-5}
        assert len(fills)>20
        mapping={}
        for rgb in fills:
            idx=np.argmin(np.linalg.norm(samples-np.array(rgb),axis=1))
            gray=float(colormaps['Greys'](idx/255)[0])
            mapping[rgb]=(gray,gray,gray)
        def substitute(match):
            rgb=tuple(float(match[i]) for i in [1,2,3])
            candidate=min(mapping,key=lambda k:sum((a-b)**2 for a,b in zip(k,rgb)))
            if max(abs(a-b) for a,b in zip(candidate,rgb))<2e-6:
                return (' '.join(f'{v:.9f}' for v in mapping[candidate])+' rg').encode()
            return match[0]
        number=rb'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
        pattern=re.compile(number+rb'\s+'+number+rb'\s+'+number+rb'\s+rg\b')
        count=0
        for xref in range(1,doc.xref_length()):
            if not doc.xref_is_stream(xref):continue
            stream=doc.xref_stream(xref)
            if b' rg' not in stream:continue
            changed=pattern.sub(substitute,stream)
            if changed!=stream:doc.update_stream(xref,changed);count+=1
        # The original population colorbar is a raster strip; preserve its
        # support and resolution while applying the identical ordinal palette.
        for image in page.get_images():
            xref=image[0]
            pix=fitz.Pixmap(doc,xref)
            if pix.n!=3:pix=fitz.Pixmap(fitz.csRGB,pix)
            pixels=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3)
            unique,inverse=np.unique(pixels.reshape(-1,3),axis=0,return_inverse=True)
            indices=np.argmin(np.sum((unique[:,None,:]/255-samples[None,:,:])**2,axis=2),axis=1)
            gray=np.round(colormaps['Greys'](indices/255)[:,:3]*255).astype(np.uint8)
            rgb=gray[inverse].reshape(pixels.shape)
            from PIL import Image
            image_bytes=io.BytesIO();Image.fromarray(rgb).save(image_bytes,format='PNG')
            page.replace_image(xref,stream=image_bytes.getvalue())
        after=page.get_drawings()
        assert len(before)==len(after)
        geometry=lambda ds:[{k:repr(v) for k,v in d.items() if k not in ['seqno','layer','fill']} for d in ds]
        assert geometry(before)==geometry(after)
        return finish(doc),dict(population_palette='Greys',paint_colors_changed=len(fills),
             streams_changed=count,colorbar_resolution_preserved=True,
             all_geometry_and_nonfill_properties_unchanged=True)


def centered_titles(stem, raw):
    """Center each heading on its panel, retaining its row and dense-panel size."""
    centers={
        'Main/Fig02':[132,394,132,394], 'Main/Fig03':[154,408,262.2,148,384],
        'Main/Fig07':[259.2,259.2,145,394],
        'Supplement/FigS01':[262.2,262.2], 'Supplement/FigS02':[262.2,262.2],
        'Supplement/FigS04':[153,413,153,413],
        'Supplement/FigS06':[262.2,262.2,132.3,394.6],
        'Supplement/FigS07':[262.2,262.2],
        'Supplement/FigS08':[262.2,262.2,262.2],
    }
    if stem not in centers:return raw,dict(existing_centered_titles_retained=True)
    with fitz.open(stream=raw,filetype='pdf') as doc:
        p=doc[0]
        old=sorted([s for s in spans(p) if re.match(r'^[A-H]\. ',s['text'].replace('\u00a0',' '))],key=lambda s:s['text'][0])
        assert len(old)==len(centers[stem]),stem
        labels=[s['text'].replace('\u00a0',' ').replace('\u00ad','-') for s in old]
        if stem=='Supplement/FigS08':labels=[label+' repair priority' for label in labels]
        font=fonts(doc,True,''.join(labels))
        if stem=='Main/Fig03':
            # Its rotated damage-state label reaches into the heading row.
            # Omit heading rectangles, never a full-width horizontal strip.
            out=cut_text(doc,[dict(s,bbox=tuple(fitz.Rect(s['bbox'])+(-1.5,-1.5,1.5,1.5))) for s in old])
            p=out[0]
            for s,label,x in zip(old,labels,centers[stem]):title(p,label,x,s['bbox'][1],font,center=True)
            result=finish(out);out.close()
            return result,dict(title_centers_pt=centers[stem],font_pt=9.5,
                original_vector_streams_reused=True,rotated_y_label_preserved=True)
        # Headings occupy empty horizontal bands. Clip those bands rather than
        # editing shared PDF text operators, which can displace unrelated text.
        bands=[]
        for s in sorted(old,key=lambda s:s['bbox'][1]):
            lo,hi=s['bbox'][1]-.2,s['bbox'][3]+.2
            if bands and lo<bands[-1][1]+1:bands[-1][1]=max(bands[-1][1],hi)
            else:bands.append([lo,hi])
        out=fitz.open();p=out.new_page(width=doc[0].rect.width,height=doc[0].rect.height)
        lo=0.
        for a,b in bands:
            if a>lo:tile(p,doc,(0,lo,p.rect.width,a))
            lo=b
        if lo<p.rect.height:tile(p,doc,(0,lo,p.rect.width,p.rect.height))
        for s,label,x in zip(old,labels,centers[stem]):title(p,label,x,s['bbox'][1],font,center=True)
        result=finish(out);out.close()
        return result,dict(title_centers_pt=centers[stem],font_pt=9.5,
                          omitted_label_rectangles=[s['bbox'] for s in old],
                          original_vector_streams_reused=True)
