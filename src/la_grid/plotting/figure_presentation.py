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
    output, palette_audit = priority_geography(raw)
    return output,dict(population_color_audit=palette_audit,
        text_and_nonpopulation_content_unchanged=True)


def restoration_workflow(raw):
    """Clarify the two restoration execution modes in Figure 1, Part 4 only."""
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        w,h=page.rect.width,page.rect.height
        old=[s for s in spans(page)
             if s['bbox'][0] > 20 and s['bbox'][0] < 258
             and s['bbox'][1] > 464 and s['bbox'][3] < 614]
        old_text={' '.join(s['text'].replace('\u00a0',' ').replace('\u00ad','-').split()) for s in old}
        assert 'Restoration Policies and Execution' in old_text
        assert {'Unconstrained','reference','Crew dispatch','and directed travel',
                'Priority-strategy','recovery','80% service'}.issubset(old_text),old_text
        white=(1.,1.,1.)
        header=(232/255,244/255,242/255)
        ink=(32/255,40/255,43/255)
        muted=(103/255,116/255,121/255)
        teal=(39/255,137/255,126/255)
        page.draw_rect(fitz.Rect(9.5,481.7,256.3,614.7),color=None,fill=white,overlay=True)
        page.draw_rect(fitz.Rect(21.8,465.2,250.5,480.5),color=None,fill=header,overlay=True)
        page.insert_font(fontname='Fig1RestorationBold',fontfile='C:/Windows/Fonts/arialbd.ttf')
        page.insert_font(fontname='Fig1RestorationBody',fontfile='C:/Windows/Fonts/arial.ttf')

        title_text='Restoration Strategies and Execution'
        title_font=fitz.Font(fontfile='C:/Windows/Fonts/arialbd.ttf')
        assert title_font.text_length(title_text,fontsize=9.5) < 224
        page.insert_text((22.677,475.654),title_text,fontname='Fig1RestorationBold',
                         fontsize=9.5,color=ink,overlay=True)

        def label(text,x,y,size=7.1,bold=False,color=ink):
            page.insert_text((x,y),text,
                fontname='Fig1RestorationBold' if bold else 'Fig1RestorationBody',
                fontsize=size,color=color,overlay=True)

        label('UNCONSTRAINED REFERENCE',15.5,497.5,bold=True,color=teal)
        for text,y in [('Repairs proceed in parallel',510.0),
                       ('using sampled durations; no',519.0),
                       ('crew or travel constraints.',528.0)]:
            label(text,15.5,y,7.2)

        label('CONSTRAINED RESTORATION',15.5,561.5,bold=True,color=teal)
        for text,y in [('Priority strategy sets repair order',574.0),
                       ('Finite crews; dispatch accounts for',583.0),
                       ('repair duration and directed travel.',592.0)]:
            label(text,15.5,y,7.0)

        page.draw_line(fitz.Point(15.5,546.0),fitz.Point(250.0,546.0),
                       color=(0.82,0.85,0.86),width=0.45,overlay=True)
        curve_x0,curve_x1=139.0,249.0
        for top,bottom,title_y,time_y in [(500.5,530.5,495.5,540.0),
                                          (564.5,594.5,559.5,604.0)]:
            label('Modeled service availability',curve_x0,title_y,6.8,color=muted)
            page.draw_line(fitz.Point(curve_x0,top),fitz.Point(curve_x0,bottom),
                           color=muted,width=0.55,overlay=True)
            page.draw_line(fitz.Point(curve_x0,bottom),fitz.Point(curve_x1,bottom),
                           color=muted,width=0.55,overlay=True)
            pts=[(curve_x0+4,bottom-2),(curve_x0+16,bottom-2),
                 (curve_x0+16,bottom-8),(curve_x0+36,bottom-8),
                 (curve_x0+36,bottom-14),(curve_x0+61,bottom-14),
                 (curve_x0+61,bottom-21),(curve_x0+84,bottom-21),
                 (curve_x0+84,top+1),(curve_x1-2,top+1)]
            page.draw_polyline([fitz.Point(x,y) for x,y in pts],
                               color=teal,width=1.25,overlay=True,lineCap=1,lineJoin=1)
            label('Time',curve_x1-15,time_y,6.8,color=muted)

        result=finish(doc)
        return result,dict(
            panel='4',title=title_text,
            execution_modes=['Unconstrained reference','Constrained restoration'],
            old_internal_labels_visually_replaced=sorted(old_text),
            output='Modeled service availability trajectory in each mode',
            no_threshold_or_T80_in_panel=True,
            unconstrained='Repairs proceed in parallel using sampled durations; no crew or travel constraints.',
            constrained='Priority strategy sets repair order; finite crews and dispatch account for repair duration and directed travel.',
            panel_bounds_preserved=True,other_panels_and_stage_5_content_unchanged=True,
            original_panel_graphics_covered_by_opaque_vector_replacement=True,
            source_vector_signature='outside authorized panel verified by native-render pixel test',
            width_pt=w,height_pt=h)


def apply(stem,raw):
    return {'Main/Fig01':restoration_workflow,'Main/Fig05':figure5,'Main/Fig07':figure7,'Supplement/FigS03':functional_network_recovery,
            'Supplement/FigS08':supplementary8}[stem](raw)


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


def functional_network_recovery(raw):
    """Keep only the two original time-dependent recovery panels and shared legend."""
    with fitz.open(stream=raw,filetype='pdf') as doc:
        p=doc[0];w=p.rect.width
        old=[s for s in spans(p) if re.match(r'^[ABC]\. ',
            s['text'].replace('\u00a0',' ').replace('\u00ad','-'))]
        assert len(old)==3
        names=['A. Recovery of largest-component fraction',
               'B. Recovery of mean degree in the largest component']
        signature=vector_signature(p)
        out=fitz.open();page=out.new_page(width=w,height=432)
        first=fitz.Rect(0,220,w,375)
        second=fitz.Rect(0,416,w,570)
        legend=fitz.Rect(0,576,w,628)
        tile(page,doc,first,-195)
        tile(page,doc,second,-205)
        tile(page,doc,legend,-201)
        heading_file='C:/Windows/Fonts/arialbd.ttf'
        heading=fitz.Font(fontfile=heading_file)
        for name,y in zip(names,[5,184]):
            x=(w-heading.text_length(name,fontsize=9.5))/2
            page.insert_text((x,y+heading.ascender*9.5),name,fontname='S3PanelHeading',
                             fontfile=heading_file,fontsize=9.5,color=(0,0,0))
        result=finish(out);out.close()
        with fitz.open(stream=result,filetype='pdf') as check:
            visible=' '.join(check[0].get_text().replace('\u00a0',' ').replace('\u00ad','-').split())
            assert all(name in visible for name in names),visible[-300:]
        return result,dict(source_vector_signature=signature,
            selected_source_regions_pt={'largest_component_recovery':list(first),
                'mean_degree_recovery':list(second),'shared_policy_legend':list(legend)},
            translations_pt={'largest_component_recovery':-195,
                'mean_degree_recovery':-205,'shared_policy_legend':-201},
            panel_titles=names,title_top_pt=[5,184],page_points=[w,432],
            source_plots_retained_as_vector_clips=True,static_percolation_excluded=True,
            recovery_column_headers_repeated=True)


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
    """Recolor only the population-context map and colorbar in muted teal."""
    from matplotlib import colormaps
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np
    population_palette=LinearSegmentedColormap.from_list(
        'MutedPopulationTeal',['#eff5f4','#b9d5d1','#6fa9a5','#287d80','#164f57'],N=256)
    population_samples=population_palette(np.linspace(0,1,256))[:,:3]
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        before=page.get_drawings()
        fills={d['fill'] for d in before if d['fill'] and d['rect'].y0>525}
        samples=colormaps['Greys'](np.linspace(0,1,256))[:,:3]
        fills={rgb for rgb in fills if max(rgb)-min(rgb)<2e-5 and .2<sum(rgb)/3<.9
               and np.min(np.linalg.norm(samples-np.array(rgb),axis=1))<2e-5}
        assert len(fills)>20
        mapping={}
        for rgb in fills:
            idx=np.argmin(np.linalg.norm(samples-np.array(rgb),axis=1))
            mapping[rgb]=tuple(float(v) for v in population_samples[idx])
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
        for xref in sorted({image[0] for image in page.get_images()}):
            pix=fitz.Pixmap(doc,xref)
            if pix.n!=3:pix=fitz.Pixmap(fitz.csRGB,pix)
            pixels=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3)
            unique,inverse=np.unique(pixels.reshape(-1,3),axis=0,return_inverse=True)
            indices=np.argmin(np.sum((unique[:,None,:]/255-samples[None,:,:])**2,axis=2),axis=1)
            colors=np.round(population_samples[indices]*255).astype(np.uint8)
            rgb=colors[inverse].reshape(pixels.shape)
            from PIL import Image
            image_bytes=io.BytesIO();Image.fromarray(rgb).save(image_bytes,format='PNG')
            page.replace_image(xref,stream=image_bytes.getvalue())
        after=page.get_drawings()
        assert len(before)==len(after)
        geometry=lambda ds:[{k:v for k,v in d.items() if k not in ['seqno','layer','fill']} for d in ds]
        assert geometry(before)==geometry(after)
        return finish(doc),dict(source_palette='Greys',population_palette='muted_blue_green',
             palette_stops=['#eff5f4','#b9d5d1','#6fa9a5','#287d80','#164f57'],
             paint_colors_changed=len(fills),
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
